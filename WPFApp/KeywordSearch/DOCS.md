Keyword Search
==============

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

## Implementation

The application window contains only two main components - a search box and a grid of
images based on a search phrase. The search box is a custom control
(see `SuggestionTextBox`) displaying suggestions. The grid is a standard `ItemsControl`.
In order to display suggestions when any text is typed, the search box needs
a reference to an implementation of `ISuggestionProvider`. Similarly when a user
presses enter to search, the search box calls `Search` on an implementation of
`ISearchProvider`.

Both providers mentioned above need to access labels provided by `LabelProvider`.
When suggestion or search results are ready, event is triggered to update
suggestions or display the search results. Thus `SuggestionTextBox` has to register
a callback from `SuggestionProvider` and `ImageProvider` a callback from the user interface.
For further details, see the figure below or directly the project with the program logic.

#### Program logic

All references established in constructor of `MainWindow`.

```
     ImageList                          App
  (ItemsControl) <-----+                 |
                       |                 ˅
NotFoundMessageBox <---+----------- MainWindow -------------+
 (ContentControl)      |             ˄   |                  |
                       |     _______/    |                  |
                       ˅    /            ˅                  ˅
                 ImageProvider --> LabelProvider <-- SuggestionProvider
                      | ˄                |            /     ˄
                      | |                ˅           /      |
                      | |          classes.labels   /       |
                      | |           (label file)   /        |
                      | |                         ˅         |
       files.index <--+ +------- SuggestionTextBox ---------+
       (index file)             (custom UI element)


        Legend:   | or -- ... reference
                  / or __ ... delegate to a function
```

#### Example flow

```
           STARTUP             SUGGESTIONS                    SEARCH

              +-- ImageProvider
             /    > LoadFromFile()
            /
           +-- LabelProvider
          /    > LoadFromFile()
         /
        /                +-- SearchProvider ---+        +-- ImageProvider --+
       /                /    > GetSuggestions() \      /    > Search()       \
      /                /                         \    /                       \
App -+-- MainWindow --+-------- UI Thread --------+--+------- UI Thread -------+-- END
```
