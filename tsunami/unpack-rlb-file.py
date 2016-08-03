#!/usr/bin/python

import json
import os
import struct
import sys

import unpack_tsunami_font

BLOCK_HEADER_SIZE = 6
BLOCK_SIGNATURE = "TMI-"
ENTRY_SIZE = 12
RESOURCE_TYPE_MESSAGE = 6
RESOURCE_TYPE_FONT = 7

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

        if block_type == RESOURCE_TYPE_FONT or block_type == RESOURCE_TYPE_MESSAGE:
            #print "resource #%d, type %d @ offset 0x%X" % (res_num, block_type, block_offset)
            (resource_type, entry_count) = struct.unpack("BB", header[4:6])
            if entry_count > 1:
                print "don't know how to handle font or message resources with more than one entry"
                sys.exit(1)
            if resource_type != block_type:
                print "resource type mismatch (index says %d, block says %d)" % (block_type, resource_type)

            # read the single resource entry
            entry = rlb.read(ENTRY_SIZE)
            (resource_id, comp_size, uncomp_size, high, res_type, offset) = \
                struct.unpack("<HHHBBI", entry)
            #print "  id %d, type %d, sizes: (%d, %d, %d), offset = 0x%X" % (resource_id, res_type, comp_size, uncomp_size, high, offset)

            if comp_size != uncomp_size:
                print "Decompression not implemented yet"
                sys.exit(1)

            rlb.seek(block_offset + offset, 0)
            payload = rlb.read(uncomp_size)

            if block_type == RESOURCE_TYPE_FONT:
                filename = "%s/resource-font-%d.dat" % (resource_dir, res_num)
                print " dumping font %d -> '%s'" % (res_num, filename)
                open(filename, "wb").write(payload)
                font_dir = "%s/resource-font-%d" % (resource_dir, res_num)
                if not os.path.exists(font_dir):
                    os.makedirs(font_dir)
                unpack_tsunami_font.unpack_font(open(filename, "rb"), font_dir)
            elif block_type == RESOURCE_TYPE_MESSAGE:
                message_list = []
                message = ""
                for j in xrange(uncomp_size):
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
        i += 6

