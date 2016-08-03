#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import struct
import sys

import pack_tsunami_font

MAIN_HEADER_SIZE = 32
BLOCK_HEADER_SIZE = 6
BLOCK_SIGNATURE = "TMI-"
ENTRY_SIZE = 12
RESOURCE_TYPE_MESSAGE = 6
RESOURCE_TYPE_FONT = 7
FONT_HEADER_SIZE = 12

SPANISH_UNICODE_MAP = {
    u"¿": 128,
    u"¡": 129,
    u"Á": 130,
    u"É": 131,
    u"Í": 132,
    u"Ó": 133,
    u"Ú": 134,
    u"Ü": 135,
    u"Ñ": 136,
    u"á": 137,
    u"é": 138,
    u"í": 139,
    u"ó": 140,
    u"ú": 141,
    u"ü": 142,
    u"ñ": 143
}

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print "USAGE: repack-rlb-file.py <original.rlb> <new.rlb> </path/to/resource/files>"
        sys.exit(1)

    # make sure the resources directory is present
    resource_dir = sys.argv[3]
    if not os.path.exists(resource_dir):
        print resource_dir + " does not exist"
        sys.exit(1)

    # open files
    if sys.argv[1] == sys.argv[2]:
        print "original and new RLB files cannot be the same"
        sys.exit(1)
    original_rlb = open(sys.argv[1], "rb")
    new_rlb = open(sys.argv[2], "wb")

    # read the main header
    header = original_rlb.read(MAIN_HEADER_SIZE)
    if header[0:4] != BLOCK_SIGNATURE:
        print "invalid block signature"
        sys.exit(1)
    (resource_type, entry_count) = struct.unpack("BB", header[4:6])
    (resource_id, comp_size, uncomp_size, high, res_type, index_offset) = \
        struct.unpack("<HHHBBI", header[6:18])
    #print "index @ 0x%X, %d bytes" % (index_offset, uncomp_size)

    # copy the header to the output, unmodified for now
    new_rlb.write(header)

    # load the index
    original_rlb.seek(index_offset, 0)
    index = original_rlb.read(uncomp_size)
    resources = []
    i = 0
    while 1:
        (res_num, block_type, block_offset) = struct.unpack("<HHH", index[i:i+6])

        if res_num == 0xFFFF and block_type == 0xFFFF and block_offset == 0xFFFF:
            # stuff a final, fake resource entry to communicate the end of data offset
            resource = {}
            resource['res_num'] = 0xFFFF
            resource['block_type'] = 0xFFFF
            resource['block_offset'] = index_offset
            resources.append(resource)
            break

        offset_high_bits = block_type >> 5
        block_type &= 0x1F
        block_offset = (block_offset | (offset_high_bits << 16)) * 16

        # check that the block has a valid signature
        original_rlb.seek(block_offset, 0)
        header = original_rlb.read(BLOCK_HEADER_SIZE)
        if header[0:4] != BLOCK_SIGNATURE:
            print "  **** block does not have 'TMI-' signature"
            sys.exit(1)

        resource = {}
        resource['res_num'] = res_num
        resource['block_type'] = block_type
        resource['block_offset'] = block_offset
        resources.append(resource)

        i += 6

    # iterate over the resources and copy them
    print "Copying %d resources..." % (len(resources))
    for i in xrange(len(resources) - 1):
        resource = resources[i]
        size = resources[i+1]['block_offset'] - resource['block_offset']
#        print "resource %d, type %d @ 0x%X, size = %d (0x%X) bytes" % (resource['res_num'], resource['block_type'], resource['block_offset'], size, size)

        # make a note of the current offset for the updated index, and to
        # overwrite size information later
        new_block_offset = new_rlb.tell()
        original_rlb.seek(resource['block_offset'], 0)

        if resource['block_type'] == RESOURCE_TYPE_MESSAGE and resource['res_num'] == 100:
            # copy over the resource header and the single entry header
            print "Substituting message resource %d" % (resource['res_num'])
            header = original_rlb.read(BLOCK_HEADER_SIZE + ENTRY_SIZE)
            new_rlb.write(header)
            (sig, res_type, res_count, res_id, comp_size, uncomp_size, hi_nib, r_type, offset) = struct.unpack("<IBBHHHBBI", header)

            new_size = 0
            if resource['res_num'] == 100:
                # copy over the padding between the header and the start of the payload
                padding_size = offset - (BLOCK_HEADER_SIZE + ENTRY_SIZE)
                new_rlb.write(original_rlb.read(padding_size))

                # iterate through the message strings for this resource and pack them
                message_filename = "%s/messages-%04d.json.txt" % (resource_dir, resource['res_num'])
                if not os.path.exists(message_filename):
                    print "Can't find file '%s' which should contain messages for resource block %d" % (message_filename, resource['res_num'])
                    sys.exit(1)
                message_list = json.loads(open(message_filename, "r").read())
                message_payload = ""
                for message in message_list:
                    for c in message['Spanish']:
                        if c in SPANISH_UNICODE_MAP:
                            print "got a Spanish character: " + c
                            message_payload += struct.pack("B", SPANISH_UNICODE_MAP[c])
                        else:
                            message_payload += struct.pack("B", ord(c))
                        new_size += 1
                    message_payload += struct.pack("B", 0)
                    new_size += 1

                # record the payload
                new_rlb.write(message_payload)

                # rewind to the header and record the new size
                current_offset = new_rlb.tell()
                new_rlb.seek(new_block_offset + 8)
                if new_size > 65535:
                    print "Hey! need to encode high nibbles!"
                    sys.exit(1)

                # write the size twice (both the compressed and uncompressed sizes)
                new_rlb.write(struct.pack("<HH", new_size, new_size))

                # forward to the end of the new block
                new_rlb.seek(current_offset, 0)

        elif resource['block_type'] == RESOURCE_TYPE_FONT:
            # sort out the new font
            font_file = "%s/resource-font-%d.dat" % (resource_dir, resource['res_num'])
            font_dir = "%s/resource-font-%d" % (resource_dir, resource['res_num'])
            font_header = open(font_file, "rb").read(FONT_HEADER_SIZE)
            font_data = pack_tsunami_font.pack_font(font_header, font_dir)
            font_data_size = len(font_data)

            # unpack the resource header and the single entry header
            header = original_rlb.read(BLOCK_HEADER_SIZE + ENTRY_SIZE)
            (sig, res_type, res_count, res_id, comp_size, uncomp_size, hi_nib, r_type, offset) = struct.unpack("<IBBHHHBBI", header)
            print "Substituting font resource #%d" % (resource['res_num'])

            # repack the header with the new font size and write the header
            header = struct.pack("<IBBHHHBBI", sig, res_type, res_count, res_id, font_data_size, font_data_size, hi_nib, r_type, offset)
            new_rlb.write(header)

            # copy over the padding between the header and the start of the payload
            padding_size = offset - (BLOCK_HEADER_SIZE + ENTRY_SIZE)
            new_rlb.write(original_rlb.read(padding_size))

            # write the new font data
            new_rlb.write(font_data)

        else:
            new_rlb.write(original_rlb.read(size))

        # save the new block offset for the new index
        resource['block_offset'] = new_block_offset

        # align the current offset to a 16-byte boundary
        current_offset = new_rlb.tell()
        if current_offset & 0xF:
            new_rlb.seek(16 - (current_offset & 0xF), 1)

    # write the new index
    print "Writing the new index..."
    index_offset = new_rlb.tell()
    for i in xrange(len(resources)):
        resource = resources[i]

        if resource['res_num'] == 0xFFFF:
            block_type = 0xFFFF
            block_offset = 0xFFFF
        else:
            block_type = resource['block_type']
            block_offset = resource['block_offset']

            block_offset >>= 4
            block_type |= (((block_offset & 0xFFFF0000) >> 11) & 0xFFFF)
            block_offset &= 0xFFFF

        new_rlb.write(struct.pack("<HHH", resource['res_num'], block_type, block_offset))

    # rewind and adjust the header
    new_rlb.seek(0x0E, 0)
    new_rlb.write(struct.pack("<I", index_offset))

    original_rlb.close()
    new_rlb.close()
