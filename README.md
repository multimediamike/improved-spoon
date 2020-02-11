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
4. './repack-rlb-file.py /path/to/original.rlb new.rlb resources/': This will combine the original RLB file and the modified resources into a new RLB file.

## Missing on Lost Island
The Python script `missing-on-lost-island/extract-data-files.py` is able to disassemble the files stored inside the Data.dat file of the game [Missing on Lost Island](http://www.mobygames.com/game/missing-on-lost-island).

## Duke Grabowski: Mighty Swashbuckler!
The Python scripts in the `duke-grabowski/` directory help with translating subtitle files from the adventure game [Duke Grabowski: Mighty Swashbuckler](https://www.kickstarter.com/projects/venture-moon/duke-grabowski-mighty-swashbuckler-point-and-click). The subtitles in this game are stored in files with the extension LDT, e.g., INTRO_TEXT_EN.LDT contains the English text for the introductory video. These files are obfuscated with a key hardcoded in the program's code. This key is necessary for running these tools.

Visit [this page](http://wiki.xentax.com/index.php/Duke_Grabowski_LDT) for more information on the LDT format as well as how to recover the obfuscation key.

Workflow:

1. './ldt2json.py FILE.LDT "key-material" FILE.json': This command will de-obfuscate FILE.LDT using the specified key and dump the subtitles into FILE.json.
2. Translate the strings inside of FILE.json. Each string is shown twice, once with the key 'original' for reference and once with the key 'translated', which will be used for the next step.
3. './json2ldt.py FILE.json "key-material" NEW_FILE.LDT': This command will use the translated strings in FILE.json and create a new subtitle file named NEW_FILE.LDT that can be read by the Duke Grabowski engine.

When specifying the key to the various command lines, enclose it with quotes and be sure to escape any special characters. 

For basic testing, unpacking an LDT to a JSON file and immediately repacking it to a new LDT should produce a new LDT file that is bit-identical to the original LDT file.

## Armed and Delirious
The Python scripts in the `armed-and-delirious/` directory help with translating subtitle files from the adventure game [Armed and Delirious](https://www.mobygames.com/game/armed-delirious). The subtitles in this game are contained in a file named SENTENCE.BIN.

Workflow:

1. './sentence.bin2json.py SENTENCE.BIN strings.json': This command will extract the strings into strings.json.
2. Translate the strings inside of strings.json. Each string is shown twice, once with the key 'original' for reference and once with the key 'translated', which will be used for the next step.
3. './json2sentence.bin.py strings.json NEW_SENTENCE.BIN': This command will use the translated strings in strings.json and create a new subtitle file named NEW_SENTENCE.BIN that can be read by the Armed and Dangerous engine.

For basic testing, unpacking SENTENCE.BIN to a JSON file and immediately repacking it to a new SENTENCE.BIN file should produce a new file that is bit-identical to the original file.

## The Hardy Boys: The Hidden Theft
The Python script `xpec-csv/xpec-binary2text-csv.py` can convert binary CSV files found on the Wii version of [The Hardy Boys: The Hidden Theft](http://www.mobygames.com/game/hardy-boys-the-hidden-theft) into a textual CSV file that should be able to be used on the PC version of the same game.

[This page describes the 2 different CSV variants in play.](http://wiki.xentax.com/index.php/CSV)

## Visionaire VED
The directory `visionaire-ved` contains 2 Python scripts for manipulating the strings in a .ved XML file generated by [Visionaire Studio](https://www.visionaire-studio.net/).

Workflow:

1. 'ved2json.py input.ved strings.json': This command will dig through input.ved and find all the unique strings inside. It will generate a list of all the strings and output them into strings.json.
2. Translate the strings inside of strings.json. Each string is shown twice, once with the key 'original' for reference and once with the key 'translated', which will be used for the next step.
3. 'json2ved.py strings.json input.ved output.ved': This command will read the original input.ved resource, replace the original strings with translated strings based on strings.json, and then generate a new ved resource file named output.ved

## SCUMM Tools
The directory `scummtools` contains scripts for manipulating the hierarchical data files found on SCUMM games. This is a list of the games that have been tested with these tools:

1. Pajama Sam: No Need to Hide When It's Dark Outside: The tool operates on the pajama.he0 and pajama.he1 files.

Workflow (for Pajama Sam):

1. Decrypt the relevant files. Example: 'crypt.py encrypted-file decrypted-file 69'.
2. Dump the strings and fonts into a new directory named pj1-strings-fonts: 'dump-strings-and-fonts.py decrypted-original.he1 pj1-strings-fonts'.
3. Edit pj1-strings-fonts/strings.json and translate the Spanish strings (do not touch the English strings since they need to remain the same for the repackaging step).
4. Repack the strings into a new resource file: 'repack-strings-and-fonts.py decrypted-original.he1 decrypted-new.he1 pj1-strings-fonts'.
5. Rebuild the HE0 index file: 'rebuild-he0-index.py original-decrypted.he0 new-decrypted.he0 new-decrypted.he1'.
6. Re-encrypt the new files. Example: 'crypt.py decrypted-file encrypted-file 69'.

## Sierra Tools
The directory `sierra` contains utilities for manipulating data files in Sierra games.

The program 'dump-rbt-frames' will take a .rbt animation file and create a series of individual PNM files.
