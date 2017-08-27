SuggestionTextBox
=================

1. Add a reference to this project
2. Add to your XAML file following:

    ```xml
    <Window ...
        xmlns:tools="clr-namespace:CustomElements;assembly=SuggestionTextBox"
        ... >
    ```
    ```xml
        <Window.Resources>
            ...
            <DataTemplate x:Key="ImageClassTemplate">
                <TextBlock Text="{Binding Path=<!--PROPERTY TO DISPLAY-->}"/>
            </DataTemplate>
            ...
        </Window.Resources>
    ```
    ```xml
        <tools:SuggestionTextBox x:Name="SuggestionTextBox"
            ItemTemplate="{StaticResource ResourceKey=ImageClassTemplate}">

            <tools:SuggestionTextBox.LoadingPlaceholder>
                <TextBlock Text="Loading..."/>
            </tools:SuggestionTextBox.LoadingPlaceholder>
        </tools:SuggestionTextBox>
    ```
3. Add to your C# code:
    ```csharp
    var Box = (SuggestionTextBox)FindName("SuggestionTextBox");
    Box.SuggestionProvider = new SuggestionProvider(); // (your implementation)
    Box.SearchProvider = new SearchProvider(); // (your implementation)
    ```
4. To update suggestions, call `OnSuggestionUpdate(IEnumerable<IIdentifiable> suggestions, string filter)`{:.language-csharp}. It is callable from any thread since internally it calls `BeginInvoke` on `Application.Current.Dispatcher`{:.language-csharp}.
5. To show message other than *Loading...* or show an exception in `MessageBox`, call `OnShowSuggestionMessage(SuggestionMessageType type, string message)`{:.language-csharp} (callable from any thread).
6. Done :)
---

##### Initialiation
Initialization is done in overwritten `OnApplyTemplate` method where references to UI parts are assigned and all event handlers registered.

##### Custom Properties
See *Properties* region in `SuggestionTextBox.cs`.

##### Public Methods
Public methods are only `OnSuggestionUpdate(IEnumerable<IIdentifiable> suggestions, string filter)`{:.language-csharp} and `OnShowSuggestionMessage(SuggestionMessageType type, string message)`{:.language-csharp}. They can be called from any thread.

##### Control & Event Handling Methods
Used to handle user interaction with the UI element. Expected to be called only from the UI thread.
