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
5. To show message other than *Loading...*, call `Application.Current.Dispatcher`{:.language-csharp}.
---

### List of all custom SuggestionTextBox properties

```csharp
bool IsLoading // indicates if there is ongoing suggestion search
               // LoadingPlaceholder is showed
```
```csharp
bool IsPopupOpen // indicates if suggestion box is open
```
```csharp
DataTemplate ItemTemplate // represents design of an suggestion item
```
```csharp
object LoadingPlaceholder // UI element to be showed instead of suggestions when IsLoading
```
```csharp
int MaxNumberOfElements // maximal number of item to show in suggestions
```
```csharp
ISuggestionProvider SuggestionProvider
```
```csharp
ISearchProvider SearchProvider
```