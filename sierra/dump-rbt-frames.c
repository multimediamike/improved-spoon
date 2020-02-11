/*
 * dump-rbt-frames.c
 *  by Mike Melanson (mike -at- multimedia.cx)
 *
 * build with this command:
 *   gcc -g -Wall dump-rbt-frames.c -o dump-rbt-frames
 */

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LE_16(x) ((((uint8_t*)(x))[1] <<  8) | ((uint8_t*)(x))[0])

#define LE_32(x) (((uint32_t)(((uint8_t*)(x))[3]) << 24) |  \
                             (((uint8_t*)(x))[2]  << 16) |  \
                             (((uint8_t*)(x))[1]  <<  8) |  \
                              ((uint8_t*)(x))[0])

/*********************************************************************/

/* Bit reader stuff */

typedef struct
{
    uint8_t *bytestream;
    int bytestream_size;
    int index;
    uint32_t bits;
    int bits_in_buffer;
} get_bits_context;

static inline void reload_bits(get_bits_context *gb)
{
    while (gb->bits_in_buffer <= 24)
    {
        if (gb->index < gb->bytestream_size)
            gb->bits |= (gb->bytestream[gb->index++] << (24 - gb->bits_in_buffer));
        gb->bits_in_buffer += 8;
    }
}

static void init_get_bits(get_bits_context *gb, uint8_t *bytestream, int size)
{
    gb->bytestream = malloc(size);
    memcpy(gb->bytestream, bytestream, size);
    gb->bytestream_size = size;
    gb->index = 0;
    gb->bits = 0;
    gb->bits_in_buffer = 0;

    reload_bits(gb);
}

/* read bits without consuming them from the stream */
static int view_bits(get_bits_context *gb, int count)
{
    if (count >= 24)
        return -1;
    if (gb->bits_in_buffer < count)
        reload_bits(gb);
    return (gb->bits >> (32 - count));
}

/* read and consume bits from the stream */
static int read_bits(get_bits_context *gb, int count)
{
    int value;

    if (count >= 24)
        return -1;

    value = view_bits(gb, count);
    gb->bits <<= count;
    gb->bits_in_buffer -= count;

    return value;
}

static void delete_get_bits(get_bits_context *gb)
{
    free(gb->bytestream);
}

/*********************************************************************/

/* RBT functions */

#define PALETTE_COUNT 256
#define RBT_HEADER_SIZE 60
#define UNKNOWN_TABLE_SIZE (1024+512)
#define SUBTITLE_THRESHOLD 0x70
#define MILLISECONDS_PER_FRAME 100

/* VLC table */
#define VLC_SIZE 4
static struct
{
    int count;
    int value;
} lzs_vlc_table[] =
{
    /* code length = 2 bits; value = 2 */
    /* 0000 */ { 2, 2 },
    /* 0001 */ { 2, 2 },
    /* 0010 */ { 2, 2 },
    /* 0011 */ { 2, 2 },

    /* code length = 2 bits; value = 3 */
    /* 0100 */ { 2, 3 },
    /* 0101 */ { 2, 3 },
    /* 0110 */ { 2, 3 },
    /* 0111 */ { 2, 3 },

    /* code length = 2 bits; value = 4 */
    /* 1000 */ { 2, 4 },
    /* 1001 */ { 2, 4 },
    /* 1010 */ { 2, 4 },
    /* 1011 */ { 2, 4 },

    /* code length = 4 bits; value = 5 */
    /* 1100 */ { 4, 5 },

    /* code length = 4 bits; value = 6 */
    /* 1101 */ { 4, 6 },

    /* code length = 4 bits; value = 7 */
    /* 1110 */ { 4, 7 },

    /* special case */
    /* 1111 */ { 4, 8 }
};

typedef struct
{
    int version;
    int width;
    int height;
    int frame_count;
    int audio_chunk_size;
    uint8_t palette[PALETTE_COUNT * 3];
    uint8_t *video_frame_size_table;
    uint8_t *frame_size_table;
    uint8_t *frame_load_buffer;
} rbt_dec_context;

static void dump_pnm_file(char *filename, rbt_dec_context *rbt,
    uint8_t *image, int width, int height)
{
    FILE *outfile;
    uint8_t bytes[3];
    int p;
    uint8_t pixel;

    outfile = fopen(filename, "wb");
    fprintf(outfile, "P6\n%d %d\n255\n", width, height);
    for (p = 0; p < width * height; p++)
    {
        pixel = image[p];
        bytes[0] = rbt->palette[pixel*3+0];
        bytes[1] = rbt->palette[pixel*3+1];
        bytes[2] = rbt->palette[pixel*3+2];
        fwrite(bytes, 3, 1, outfile);
    }
    fclose(outfile);
}

static int load_rbt_header(rbt_dec_context *rbt, FILE *inrbt_file)
{
    uint8_t header[RBT_HEADER_SIZE];
    int palette_data_size;
    uint8_t *palette_chunk;
    int unknown_chunk_size;
    off_t padding_size;
    int i;
    int frame_size;
    int max_frame_size;
    int first_palette_index;
    int palette_count;
    int palette_type;
    int palette_index;

    fseek(inrbt_file, 0, SEEK_SET);

    /* load the header */
    if (fread(header, RBT_HEADER_SIZE, 1, inrbt_file) != 1)
    {
        printf("problem reading initial RBT header\n");
        return 0;
    }

    rbt->version = LE_16(&header[6]);
    rbt->audio_chunk_size = LE_16(&header[8]);
    rbt->frame_count = LE_16(&header[14]);

    /* skip the unknown data, if it's there */
    unknown_chunk_size = LE_16(&header[18]);
    fseek(inrbt_file, unknown_chunk_size, SEEK_CUR);

    /* load the palette chunk */
    palette_data_size = LE_16(&header[16]);
    palette_chunk = malloc(palette_data_size);
    if (fread(palette_chunk, palette_data_size, 1, inrbt_file) != 1)
    {
        printf("problem reading palette\n");
        return 0;
    }

    /* load the palette into the internal context */
    memset(rbt->palette, 0, PALETTE_COUNT * 3);
    first_palette_index = palette_chunk[25];
    palette_count = LE_16(&palette_chunk[29]);
    palette_type = palette_chunk[32];
    palette_index = (palette_type == 0) ? 38 : 37;
    for (i = first_palette_index; i < first_palette_index + palette_count; i++)
    {
        rbt->palette[i*3+0] = palette_chunk[palette_index++];
        rbt->palette[i*3+1] = palette_chunk[palette_index++];
        rbt->palette[i*3+2] = palette_chunk[palette_index++];
    }
    free(palette_chunk);

    /* load the video frame size table (2 bytes per frame) */
    rbt->video_frame_size_table = malloc(rbt->frame_count * sizeof(uint16_t));
    if (fread(rbt->video_frame_size_table, rbt->frame_count * sizeof(uint16_t), 1, inrbt_file) != 1)
    {
        printf("problem reading frame table\n");
        return 0;
    }

    /* load the frame size table (2 bytes per frame) */
    rbt->frame_size_table = malloc(rbt->frame_count * sizeof(uint16_t));
    if (fread(rbt->frame_size_table, rbt->frame_count * sizeof(uint16_t), 1, inrbt_file) != 1)
    {
        printf("problem reading frame table\n");
        return 0;
    }

    /* find the max frame size */
    max_frame_size = 0;
    for (i = 0; i < rbt->frame_count; i++)
    {
        frame_size = LE_16(&rbt->frame_size_table[i*2]);
        if (frame_size > max_frame_size)
            max_frame_size = frame_size;
    }
    rbt->frame_load_buffer = malloc(max_frame_size);

    /* skip the unknown table(s) */
    fseek(inrbt_file, UNKNOWN_TABLE_SIZE, SEEK_CUR);

    /* skip over padding */
    padding_size = 0x800 - (ftell(inrbt_file) & 0x7FF);
    fseek(inrbt_file, padding_size, SEEK_CUR);

    return 1;
}

static int get_lzs_back_ref_length(get_bits_context *gb)
{
    int vlc;
    int count;
    int value;

    vlc = view_bits(gb, VLC_SIZE);
    count = lzs_vlc_table[vlc].count;
    value = lzs_vlc_table[vlc].value;

    read_bits(gb, count);
    if (value == 8)
    {
        do
        {
            vlc = read_bits(gb, VLC_SIZE);
            value += vlc;
        }
        while (vlc == 0xF);
    }

    return value;
}

static int copy_frames(rbt_dec_context *rbt, FILE *inrbt_file,
    int window_width, int window_height)
{
    int i;
    int j;
    int scale;
    int width;
    int height;
    int max_width;
    int max_height;
    int frame_x;
    int frame_y;
    int fragment_count;
    int decoded_size;
    uint8_t *decoded_frame;
    int fragment;
    int fragment_compressed_size;
    int fragment_decompressed_size;
    int compression_type;
    int index;
    int out_index;
    get_bits_context gb;
    int frame_size;

    int back_ref_offset_type;
    int back_ref_offset;
    int back_ref_length;
    int back_ref_start;
    int back_ref_end;

    uint8_t *full_window;
    int full_window_size;
    int y;

    char filename[30];

    full_window_size = window_width * window_height;
    full_window = malloc(full_window_size);

    max_width = 0;
    max_height = 0;

    for (i = 0; i < rbt->frame_count; i++)
    {
        /* read the entire frame (includes audio and video) */
        frame_size = LE_16(&rbt->frame_size_table[i*2]);
        if (fread(rbt->frame_load_buffer, frame_size, 1, inrbt_file) != 1)
        {
            printf("problem reading frame %d\n", i);
            return 0;
        }

        scale = rbt->frame_load_buffer[3];
        width = LE_16(&rbt->frame_load_buffer[4]);
        if (max_width < width)
            max_width = width;
        if (max_height < height)
            max_height = height;
        height = LE_16(&rbt->frame_load_buffer[6]);
        frame_x = LE_16(&rbt->frame_load_buffer[12]);
        frame_y = LE_16(&rbt->frame_load_buffer[14]);
        fragment_count = LE_16(&rbt->frame_load_buffer[18]);
        decoded_size = width * height;

        printf("processing frame %d: %d%%, %dx%d, origin @ (%d, %d), %d fragments\n", i, scale, width, height, frame_x, frame_y, fragment_count);

        /* decode the frame */
        decoded_frame = malloc(decoded_size);
        index = 24;
        out_index = 0;
        for (fragment = 0; fragment < fragment_count; fragment++)
        {
            fragment_compressed_size = LE_32(&rbt->frame_load_buffer[index]);
            index += 4;
            fragment_decompressed_size = LE_32(&rbt->frame_load_buffer[index]);
            index += 4;
            compression_type = LE_16(&rbt->frame_load_buffer[index]);
            index += 2;

            if (compression_type == 0)
            {
                init_get_bits(&gb, &rbt->frame_load_buffer[index],
                    fragment_compressed_size);

                while (out_index < fragment_decompressed_size)
                {
                    if (read_bits(&gb, 1))
                    {
                        /* decode back reference offset type */
                        back_ref_offset_type = read_bits(&gb, 1);

                        /* back reference offset is 7 or 11 bits */
                        back_ref_offset = read_bits(&gb,
                            (back_ref_offset_type) ? 7 : 11);

                        /* get the length of the back reference */
                        back_ref_length = get_lzs_back_ref_length(&gb);
                        back_ref_start = out_index - back_ref_offset;
                        back_ref_end = back_ref_start + back_ref_length;

                        /* copy the back reference, byte by byte */
                        for (j = back_ref_start; j < back_ref_end; j++)
                            decoded_frame[out_index++] = decoded_frame[j];
                    }
                    else
                    {
                        /* read raw pixel byte */
                        decoded_frame[out_index++] = read_bits(&gb, 8) & 0xFF;
                    }
                }

                delete_get_bits(&gb);
            }

            /* next fragment */
            index += fragment_compressed_size;
        }

        /* dump the original frame */
        sprintf(filename, "original-frame-%03d.pnm", i);
        dump_pnm_file(filename, rbt, decoded_frame, width, height);

        /* transfer the image onto the frame window */
        memset(full_window, 0xFF, full_window_size);
        index = 0;
        for (y = 0; y < height; y++)
        {
            out_index = window_width * (frame_y + y) + frame_x;
            memcpy(&full_window[out_index], &decoded_frame[index], width);
            index += width;
        }

        /* dump the frame plotted onto the full window */
        sprintf(filename, "frame-inside-window-%03d.pnm", i);
        dump_pnm_file(filename, rbt, full_window, window_width, window_height);

        free(decoded_frame);
    }

    printf("maximum dimensions seen are %dx%d\n", max_width, max_height);

    free(full_window);

    return 1;
}

int main(int argc, char *argv[])
{
    char *inrbt_filename;
    FILE *inrbt_file;
    rbt_dec_context rbt;
    int window_width;
    int window_height;
    int tr_r;
    int tr_g;
    int tr_b;

    /* validate the number of arguments */
    if (argc < 7)
    {
        printf("USAGE: dump-rbt-frames <file.rbt> <window width> <window height> <tr_r> <tr_g> <tr_b>\n");
        printf("tr_r, _g, _b allow specifying the red, green and blue values of the\ntransparent color (palette index 255).\nThese values need to be numbers between 0 and 255.\n");

        return 1;
    }
    inrbt_filename = argv[1];
    window_width = atoi(argv[2]);
    window_height = atoi(argv[3]);
    tr_r = atoi(argv[4]);
    tr_g = atoi(argv[5]);
    tr_b = atoi(argv[6]);
    printf("background/transparency color: (%d, %d, %d)\n", tr_r, tr_g, tr_b);

    inrbt_file = fopen(inrbt_filename, "rb");
    if (!inrbt_file)
    {
        perror(inrbt_filename);
        return 1;
    }

    /* process the header */
    if (!load_rbt_header(&rbt, inrbt_file))
        return 1;

    /* hijack the transparent color */
    rbt.palette[0xFF*3+0] = tr_r;
    rbt.palette[0xFF*3+1] = tr_g;
    rbt.palette[0xFF*3+2] = tr_b;

    /* rewrite the frames */
    if (!copy_frames(&rbt, inrbt_file, window_width, window_height))
        return 1;

    /* finished with file */
    fclose(inrbt_file);

    /* clean up */
    free(rbt.frame_load_buffer);
    free(rbt.video_frame_size_table);
    free(rbt.frame_size_table);

    return 0;
}
