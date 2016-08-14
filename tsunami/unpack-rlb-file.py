#!/usr/bin/python

import json
import os
import struct
import sys

import unpack_tsunami_font

BLOCK_HEADER_SIZE = 6
BLOCK_SIGNATURE = "TMI-"
ENTRY_SIZE = 12
RESOURCE_TYPE_STRIP = 1
RESOURCE_TYPE_MESSAGE = 6
RESOURCE_TYPE_FONT = 7
STRIP_STRUCT_SIZE = 126

HANDLED_RESOURCE_TYPES = [ RESOURCE_TYPE_STRIP, RESOURCE_TYPE_MESSAGE, RESOURCE_TYPE_FONT ]

def read_cstr(block, offset):
    cstr = ""
    while 1:
        c = block[offset]
        if c == '\0':
            return cstr
        else:
            cstr += c
            offset += 1

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "USAGE: unpack-rlb-file.py </path/to/file.rlb> </path/to/unpack/into>"
        sys.exit(1)

    resource_dir = sys.argv[2]

    # if the output directory already exists, don't go any farther
    if os.path.exists(resource_dir):
        print resource_dir + " already exists"
        sys.exit(1)
    os.makedirs(resource_dir)

    rlb = open(sys.argv[1], "rb")

    # read the main header
    header = rlb.read(BLOCK_HEADER_SIZE)
    if header[0:4] != BLOCK_SIGNATURE:
        print "invalid block signature"
        sys.exit(1)
    (resource_type, entry_count) = struct.unpack("BB", header[4:6])
    entry = rlb.read(ENTRY_SIZE)
    (resource_id, comp_size, uncomp_size, high, res_type, offset) = \
        struct.unpack("<HHHBBI", entry)
    print "index @ 0x%X, %d bytes" % (offset, uncomp_size)

    # load the index
    rlb.seek(offset, 0)
    index = rlb.read(uncomp_size)
    i = 0
    while 1:
        (res_num, block_type, block_offset) = struct.unpack("<HHH", index[i:i+6])
        if res_num == 0xFFFF and block_type == 0xFFFF and block_offset == 0xFFFF:
            #print "end of index"
            break
        offset_high_bits = block_type >> 5
        block_type &= 0x1F
        block_offset = (block_offset | (offset_high_bits << 16)) * 16
        #print "block type %d at 0x%X" % (block_type, block_offset)

        # check that the block has a valid signature
        rlb.seek(block_offset, 0)
        header = rlb.read(BLOCK_HEADER_SIZE)
        if header[0:4] != BLOCK_SIGNATURE:
            print "  **** block does not have 'TMI-' signature"
            sys.exit(1)

        if block_type in HANDLED_RESOURCE_TYPES:
            #print "resource #%d, type %d @ offset 0x%X" % (res_num, block_type, block_offset)
            (resource_type, entry_count) = struct.unpack("BB", header[4:6])
            if resource_type != block_type:
                print "resource type mismatch (index says %d, block says %d)" % (block_type, resource_type)

            # read all of the entries
            entries = []
            for j in xrange(entry_count):
                entry_bytes = rlb.read(ENTRY_SIZE)
                (entry_id, comp_size, uncomp_size, high, res_type, offset) = \
                    struct.unpack("<HHHBBI", entry_bytes)
                #print "  id %d, type %d, sizes: (%d, %d, %d), offset = 0x%X" % (entry_id, res_type, comp_size, uncomp_size, high, offset)

                if comp_size != uncomp_size:
                    print "Decompression not implemented yet"
                    sys.exit(1)

                cur_pos = rlb.tell()
                rlb.seek(block_offset + offset, 0)
                payload = rlb.read(uncomp_size)
                entries.append({ 'payload': payload, 'size': uncomp_size })
                rlb.seek(cur_pos, os.SEEK_SET)

            if block_type == RESOURCE_TYPE_FONT:
                filename = "%s/resource-font-%02d.dat" % (resource_dir, res_num)
                print "dumping font %d -> '%s'" % (res_num, filename)
                open(filename, "wb").write(entries[0]['payload'])
                font_dir = "%s/resource-font-%02d" % (resource_dir, res_num)
                if not os.path.exists(font_dir):
                    os.makedirs(font_dir)
                unpack_tsunami_font.unpack_font(open(filename, "rb"), font_dir)
            elif block_type == RESOURCE_TYPE_MESSAGE:
                payload = entries[0]['payload']
                size = entries[0]['size']
                message_list = []
                message = ""
                for j in xrange(size):
                    if payload[j] == '\0':
                        pair = {}
                        pair['English'] = message
                        pair['Spanish'] = message
                        message_list.append(pair)
                        message = ""
                    else:
                        if payload[j] == '\x0D':
                            message += '\n'
                        else:
                            message += payload[j]
    
                message_file = "%s/messages-%04d.json.txt" % (resource_dir, res_num)
                print "dumping message resource %d -> '%s'" % (res_num, message_file)
                open(message_file, "w").write(json.dumps(message_list, indent=2))
            elif block_type == RESOURCE_TYPE_STRIP:
                struct_count = entries[0]['size'] /  STRIP_STRUCT_SIZE
                records = entries[0]['payload']
                messages = entries[1]['payload']
                object_list = []
                for si in range(0, struct_count*STRIP_STRUCT_SIZE, STRIP_STRUCT_SIZE):
                    record = records[si:si+STRIP_STRUCT_SIZE]
                    record_id = struct.unpack("<H", record[12:14])[0]
                    message_list = []
                    for ri in range(44, 44 + (8 * 10), 10):
                        (str_id, offset) = struct.unpack("<HH", record[ri:ri+4])
                        if str_id > 0:
                            message = read_cstr(messages, offset)
                            pair = {}
                            pair['id'] = str_id
                            pair['English'] = message
                            pair['Spanish'] = message
                            message_list.append(pair)
                    speaker_offset = struct.unpack("<H", record[124:126])[0]
                    speaker = read_cstr(messages, speaker_offset)
                    object_list.append({ 'speaker': speaker, 'strings': message_list })

                    strip_file = "%s/strip-%04d.json.txt" % (resource_dir, res_num)
                    print "dumping strip resource %d -> '%s'" % (res_num, strip_file)
                    open(strip_file, "w").write(json.dumps(object_list, indent=2))

        # advance to next index entry
        i += 6

