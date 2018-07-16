VirtTool User Guide
===================

This program, and especially its logic, is used as a part of a complex tool
for Video Browser Showdown 2018 (VBS), live video search competition.
It demonstrates an ability of our tool to initiate the search for a clip
by a keyword.

The program works only with images, since videos are represented by keyframes
to save space and reduce a number of duplicates shown to user. Each image is
classified by our neural net into a few categories and is written to an index file.
The program logic then only searches the index file and provides a list of result
to the implementation of a user interface which shows correct images to a user.

A custom control element provides a user an easy way to access all possible
image categories via given suggestions. The labels used for the suggestions are loaded from a
text file pre generated outside the tool to match the neural net's categories.
These labels are also used to match users' search phrase to a correct category of the neural net.

## Before The Start
The directory where the compiled program is located need to contain exactly one *.ini*
file with the following structure:

    images=X:/path/to/image/folder
    [source_name]
    label=X:/path/to/label/for/source_name
    index=X:/path/to/inverted/index/for/source_name
    idf=X:/path/to/idf/file/for/source_name

- ***images***: Folder containing all the images that shall be displayed to the user with their name formated as `{:07d}.jpg`
                where `{:07d}` is image's id formated with leading zeros.
- ***source\_name***: Displayed in the UI as one keyword model. The file can contain multiple models.
  - ***label***: Label text file containing mapping from label ids to label names and descriptions.
                 See format detail bellow.
  - ***index***: Inverted index file mapping labels to images and their ranks. See format detail bellow.
  - ***idf***: Inverted document frequency file. This is optional, IDF is not used if idf row is missing. See format detail bellow.


#### Label File
Each label must be on its own line in folowing format:

    internal_id~synset_id~names~hyponyms~hypernyms~description

where:
- *internal\_id*: An integer under which the label is identified in the inverted index file.
                  If this label does not have any label associated in the index file and is used as a hypernym, `H` is used as its *internal\_id*.
- *synset\_id*: An integer that is used in the hypernym-hyponym relations, usually WordNet id.
- *names*: Name or list of names separated by `#`.
- *hyponyms*: List of *synset\_id*s that are direct hyponyms separated by `#`.
- *hypernyms*: List of *synset\_id*s that are direct hypernyms separated by `#`.
- *description*: String used in suggestions to give some context to the label name.

All items except *internal\_id* and *names* can be empty.


#### Inverted Index File

File's format:

	  0: 4B 53 20 49 4E 44 45 58 ('KS INDEX' in ASCII)
	  8: FF FF FF FF FF FF FF FF
	 16: table
	  X: FF FF FF FF FF FF FF FF
	X+8: (multiple) ids of class at offset X+8
	  Y: FF FF FF FF FF FF FF FF
	Y+8: similarly as at offset X+8 and Y till the end

Table's format:

	  T: unsigned 32 bit integer - class id (as in the label file)
	T+4: unsigned 32 bit integer - offset of the first file in this class

Id's format:

	  I: unsigned 32 bit integer - photo id
	I+4: float - probability the photo is in this class

#### IDF File
Format of the file is the folowing:

    42 43 00 00 00 00 00 00 00 00 00 00 00 00 00 00 | BC              
    32 30 31 38 2D 30 34 2D 30 31 20 30 30 3A 30 30 | 2018-04-01 00:00
    3A 30 30 0A TT TT TT TT XX XX XX XX XX XX XX XX | :00\n

where `T` is 32 bit integer (LE) - number of floats that follow to the end of the file and `X` are the floats.
See the thesis for more information how IDF is applied.

## Usage

The only user interaction is through the search box.
To perform a search user needs to select one of the suggestions by `Enter` (mouse click does not work).
`Up`, `Down`, `Right`, `Left` keys can be used to navigate in the suggestions.
The current query is displayed atop of the search box. To remove any part of the query or to change any logical symbol, click on it.
See the thesis for more details.

## Implementation
See the thesis for more details.

#### SuggestionTextBox

1. Add to your XAML file following:
    ```xml
    <Window xmlns:control="clr-namespace:ViretTool.BasicClient"
            ... >
        <control:KeywordSearchControl x:Name="KSC"/>
    ```
2. Add to your C# code:
    ```csharp
    labelFiles = string[] {"path/to/label/file1", "path/to/label/file2", ...}
    sourceNames = string[] {"name_of_model1", "name_of_model2", ...}

    KSC.Init(labelFiles, sourceNames);
    KSC.KeywordChangedEvent += KSC_KeywordChangedEvent;

    KSC_KeywordChangedEvent(List<List<int>> query, string annotationSource) { 
        // Compute ranking given `query` and model named `annotationSource`.
    }
    ```

#### Keyword Models

1. Add to your C# code:
    ```csharp
    indexFiles = string[] {"path/to/index/file1", "path/to/index/file2", ...}
    idfFiles = string[] {null, "path/to/idf/file2", ...} // model1 will not use IDF
    sourceNames = string[] {"name_of_model1", "name_of_model2", ...}

    var model = new KeywordModelWrapper(indexFiles, idfFiles, sourceNames);
    List<Frame> result = model.RankFramesBasedOnQuery(query, annotationSource);
    ```