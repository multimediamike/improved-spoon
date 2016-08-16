# improved-spoon
A collection of hacking/modification tools for the specific computer games.

The name 'improved-spoon' was randomly generated by GitHub while creating this repository.

## Tsunami Tools
These tools are build to operate on the data files found in Tsunami games. Presently, they are primarily built to handle the R2RW.RLB file from the game [Return to Ringworld](http://www.mobygames.com/game/dos/return-to-ringworld). Here is [documentation for the RLB file format](http://wiki.xentax.com/index.php/Tsunami_RLB).

### Programs
1. unpack-rlb-file.py: This Python script digs through the RLB file and finds all of the text strings and fonts. It collects all of the text strings and dumps them into a files in the format 'messages-####.json.txt', according to the resource ID of the message block. It dumps the font resources into files named 'resource-font-##.dat', according to the font resource ID. It dumps all strip conversation resources into files name 'strip-####.json.txt', according to the strip resource ID.
2. repack-rlb-file.py: This Python script takes an original RLB file and transfers the contents to a new RLB file, locating modified resources in the process and incorporating them in the new RLB resource file.
3. unpack_tsunami_font.py: This Python script unpacks the individual characters in a Tsunami font file into a sequence of Portable Grey Map (PGM) files which can be edited with a text editor. It also pre-populates placeholder characters for 16 additional Spanish characters. This script is called from unpack-rlb-file.py. It should not be necessary to invoke directly except for debugging.
4. pack_tsunami_font.py: This Python script finds a sequence of PGM files and encodes them into a new Tsunami font file. This is called from repack-rlb-file.py. It should not be necessary to invoke directly except for debugging.

### Workflow
Presently, the tools are designed to assist in translating a game's assets to Spanish. When the unpack tool is run, it creates a sequence of JSON files that contain each string twice: once for English and once for Spanish. The goal is to modify the Spanish string so that the repack script will incorporate it into the new RLB file.

Further, the font unpacking tool automatically adds 16 extra characters corresponding to the 16 characters needed to express Spanish text: á, é, í, ó, ú, ü, ñ (each in both upper and lower case), and the inverted punctuation marks: ¿, ¡. While the tool automatically rotates the punctuation marks, it only copies, i.e., 'n' to the right character position. It is up to the game translator to edit this character to add the correct diacritic mark.

The workflow is:

1. './unpack-rlb-file.py /path/to/original.rlb resources/': This unpacks the translateable resources from the original RLB into a directory named 'resources/'. Note that the tool will halt if the directory already exists so that it can't overwrite existing translation work.
2. Edit the font resources by adding the correct diacritic markers. This can be done using a graphic editor that supports PGM files, or a text editor since PGM files are simple text.
3. Edit the individual messages and strip files, modifying the 'Spanish' strings in each English/Spanish pair.
4 './repack-rlb-file.py /path/to/original.rlb new.rlb resources/': This will combine the original RLB file and the modified resources into a new RLB file.

## Missing on Lost Island
The Python script `missing-on-lost-island/extract-data-files.py` is able to disassemble the files stored inside the Data.dat file of the game [Missing on Lost Island](http://www.mobygames.com/game/missing-on-lost-island).
