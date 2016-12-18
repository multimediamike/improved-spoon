#!/usr/bin/python

# xpec-binary2text-csv.py
#   by Mike Melanson (mike -at- multimedia.cx)

# This program converts a binary CSV file from an XPEC game to a
# textual CSV file.
#
# USAGE: xpec-binary2text-csv.py <binary-file.csv> <text-file.csv>

import struct
import sys

FIELD_COUNT = 19
PAD_8BIT = 0xCC
PAD_16BIT = 0xCD

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "USAGE: xpec-binary2text-csv.py <binary-file.csv> <text-file.csv>"
        sys.exit(1)

    infile = sys.argv[1]
    outfile = sys.argv[2]

    # load the entire input file
    bindata = open(infile, "rb").read()
    bindata_len = len(bindata)

    # get the output ready
    csvdata = open(outfile, "wb")
    # write the byte order mark
    csvdata.write(struct.pack("BB", 0xFF, 0xFE))

    utf16le_comma = ','.encode("utf-16-le")
    utf16le_newline = '\r\n'.encode("utf-16-le")

    # First phase: figure out the lengths and types of each header field.
    # Scan and collect bytes until 0xCC or 0xCD is found. That byte
    # indicates the field type.
    fields = []
    i = 0
    for x in range(FIELD_COUNT):
        j = i
        header = ""
        # accumulate characters until padding byte is seen
        while 1:
            next_byte = struct.unpack("B", bindata[j])[0]
            if next_byte == PAD_8BIT or next_byte == PAD_16BIT:
                padding_byte = next_byte
                break
            header += bindata[j]
            j += 1

        # advance past the padding bytes
        while 1:
            next_byte = struct.unpack("B", bindata[j])[0]
            if next_byte != padding_byte:
                break
            j += 1

        field_length = j - i
        i = j
        if padding_byte == PAD_8BIT:
            header_utf8 = header.decode("utf-8")[:-1]
        else:
            header_utf8 = header.decode("utf-16-be")[:-1]
        csvdata.write(header_utf8.encode("utf-16-le"))
        if x < FIELD_COUNT - 1:
            csvdata.write(utf16le_comma)
        else:
            csvdata.write(utf16le_newline)

        fields.append( { 'padding': padding_byte, 'length': field_length } )

    # Next phase: now that the lengths and types of the fields are known,
    # load the records from the remainder of the file and convert the
    # strings.
    while i < bindata_len:
        x = 0
        for field in fields:
            if field['padding'] == PAD_8BIT:
                # search for 0x00
                for j in range(field['length']):
                    if struct.unpack("B", bindata[i+j])[0] == 0:
                        break
                field_utf8 = bindata[i:i+j].decode("utf-8")
            else:
                # search for 0x0000
                for j in range(field['length'] / 2):
                    if struct.unpack(">H", bindata[i+j*2:i+j*2+2])[0] == 0:
                        break
                field_utf8 = bindata[i:i+j*2].decode("utf-16-be")
            i += field['length']

            # Take care of extra punctuation: if there is a comma then
            # enclose the string in quotes. If there are commas and quotes
            # then escape the quotes as well.
            if u',' in field_utf8:
                if '"' in field_utf8:
                    field_utf8 = field_utf8.replace('"', '""')
                field_utf8 = '"' + field_utf8 + '"'

            # write the field
            csvdata.write(field_utf8.encode("utf-16-le"))
            if x < FIELD_COUNT - 1:
                csvdata.write(utf16le_comma)
            else:
                csvdata.write(utf16le_newline)
            x += 1

    csvdata.close()
