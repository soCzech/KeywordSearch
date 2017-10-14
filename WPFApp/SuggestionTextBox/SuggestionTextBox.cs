// inspired by: https://wpfautocomplete.codeplex.com/

using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Controls.Primitives;
using System.Windows.Media;

namespace CustomElements {
    /// <summary>
    /// Follow steps 1a or 1b and then 2 to use this custom control in a XAML file.
    ///
    /// Step 1a) Using this custom control in a XAML file that exists in the current project.
    /// Add this XmlNamespace attribute to the root element of the markup file where it is 
    /// to be used:
    ///
    ///     xmlns:MyNamespace="clr-namespace:SuggestionTextBox"
    ///
    ///
    /// Step 1b) Using this custom control in a XAML file that exists in a different project.
    /// Add this XmlNamespace attribute to the root element of the markup file where it is 
    /// to be used:
    ///
    ///     xmlns:MyNamespace="clr-namespace:SuggestionTextBox;assembly=SuggestionTextBox"
    ///
    /// You will also need to add a project reference from the project where the XAML file lives
    /// to this project and Rebuild to avoid compilation errors:
    ///
    ///     Right click on the target project in the Solution Explorer and
    ///     "Add Reference"->"Projects"->[Select this project]
    ///
    ///
    /// Step 2)
    /// Go ahead and use your control in the XAML file.
    ///
    ///     &lt;MyNamespace:SuggestionTextBox/&gt;
    ///
    /// </summary>
    public class SuggestionTextBox : Control {

        static SuggestionTextBox() {
            DefaultStyleKeyProperty.OverrideMetadata(typeof(SuggestionTextBox), new FrameworkPropertyMetadata(typeof(SuggestionTextBox)));
        }

        #region Initialization

        /// <summary>
        /// Indetifies TextBox part of the UI element
        /// </summary>
        public const string PartTextBox = "PART_TextBox";
        /// <summary>
        /// Indetifies Popup (containing list of suggestions) part of the UI element
        /// </summary>
        public const string PartPopup = "PART_Popup";
        /// <summary>
        /// Indetifies ListBox (with suggestions) part of the UI element
        /// </summary>
        public const string PartListBox = "PART_ListBox";

        private TextBox TextBox_;
        private List<Popup> Popups_;
        private Selector Selector_;

        /// <summary>
        /// Initialize the UI elements and register events
        /// </summary>
        public override void OnApplyTemplate() {
            base.OnApplyTemplate();

            TextBox_ = (TextBox)Template.FindName(PartTextBox, this);
            Popups_ = new List<Popup>();
            Popups_.Add((Popup)Template.FindName(PartPopup, this));
            Selector_ = (Selector)Template.FindName(PartListBox, this);

            TextBox_.TextChanged += TextBox_OnTextChanged;
            TextBox_.PreviewKeyDown += TextBox_OnKeyDown;
            TextBox_.LostFocus += TextBox_OnLostFocus;

            Popups_[0].StaysOpen = false;
            Popups_[0].Closed += Popup_OnClosed;
        }

        #endregion

        #region Properties

        public static readonly DependencyProperty IsPopupOpenProperty = DependencyProperty.Register("IsPopupOpen", typeof(bool), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(false));
        public static readonly DependencyProperty SuggestionProviderProperty = DependencyProperty.Register("SuggestionProvider", typeof(ISuggestionProvider), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(null));
        public static readonly DependencyProperty SearchProviderProperty = DependencyProperty.Register("SearchProvider", typeof(ISearchProvider), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(null));
        public static readonly DependencyProperty ItemTemplateSelectorProperty = DependencyProperty.Register("ItemTemplateSelector", typeof(DataTemplateSelector), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(null));
        public static readonly DependencyProperty IsLoadingProperty = DependencyProperty.Register("IsLoading", typeof(bool), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(false));
        public static readonly DependencyProperty MaxNumberOfElementsProperty = DependencyProperty.Register("MaxNumberOfElements", typeof(int), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(50));
        public static readonly DependencyProperty LoadingPlaceholderProperty = DependencyProperty.Register("LoadingPlaceholder", typeof(object), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(null));

        /// <summary>
        /// Indicates if the suggestions popup is open.
        /// </summary>
        public bool IsPopupOpen {
            get { return (bool)GetValue(IsPopupOpenProperty); }
            set { SetValue(IsPopupOpenProperty, value); }
        }

        /// <summary>
        /// Suggestion provider responsible for any suggestions
        /// </summary>
        public ISuggestionProvider SuggestionProvider {
            get { return (ISuggestionProvider)GetValue(SuggestionProviderProperty); }
            set { SetValue(SuggestionProviderProperty, value); }
        }

        /// <summary>
        /// Search provider responsibe for any results
        /// </summary>
        public ISearchProvider SearchProvider {
            get { return (ISearchProvider)GetValue(SearchProviderProperty); }
            set { SetValue(SearchProviderProperty, value); }
        }

        /// <summary>
        /// Template for items in the ListBox
        /// </summary>
        public DataTemplateSelector ItemTemplateSelector {
            get { return (DataTemplateSelector)GetValue(ItemTemplateSelectorProperty); }
            set { SetValue(ItemTemplateSelectorProperty, value); }
        }

        /// <summary>
        /// Indicates if suggestions are not ready yet
        /// </summary>
        public bool IsLoading {
            get { return (bool)GetValue(IsLoadingProperty); }
            set { SetValue(IsLoadingProperty, value); }
        }

        /// <summary>
        /// Maximal number of elements shown in suggestions (-1 implies unlimited)
        /// </summary>
        public int MaxNumberOfElements {
            get { return (int)GetValue(MaxNumberOfElementsProperty); }
            set { SetValue(MaxNumberOfElementsProperty, value); }
        }

        /// <summary>
        /// TextBlock shown if loading any results
        /// </summary>
        public object LoadingPlaceholder {
            get { return GetValue(LoadingPlaceholderProperty); }
            set { SetValue(LoadingPlaceholderProperty, value); }
        }

        #endregion

        #region Public Methods

        /// <summary>
        /// Visually update suggestions
        /// </summary>
        /// <param name="suggestions"><see cref="IEnumerable{IIdentifiable}"/> of the suggestions</param>
        /// <param name="filter">A string, the suggestions are for</param>
        public void OnSuggestionResultsReady(IEnumerable<IIdentifiable> suggestions, string filter) {
            Application.Current.Dispatcher.BeginInvoke((Action)delegate {
                if (IsPopupOpen && filter == TextBox_.Text) {
                    IsLoading = false;
                    Selector_.ItemsSource = MaxNumberOfElements < 0 ? suggestions : suggestions.Take(MaxNumberOfElements);
                    IsPopupOpen = Selector_.HasItems;
                }
            });
        }

        /// <summary>
        /// Show message in the Popup of this UI element
        /// </summary>
        public void OnShowSuggestionMessage(SuggestionMessageType type, string message) {
            Application.Current.Dispatcher.BeginInvoke((Action)delegate {
                switch (type) {
                    case SuggestionMessageType.Exception:
                        Popup_Close();
                        MessageBox.Show(message, "Exception", MessageBoxButton.OK, MessageBoxImage.Exclamation);
                        return;
                    case SuggestionMessageType.Information:
                        ((TextBlock)LoadingPlaceholder).Text = message;
                        break;
                    default:
                        MessageBox.Show("Unknown type of SuggestionError", "Error", MessageBoxButton.OK, MessageBoxImage.Exclamation);
                        break;
                }
            });
        }

        #endregion

        #region Control Methods

        private void Popup_Open() {
            IsPopupOpen = true;
            IsLoading = true;

            Selector_.ItemsSource = null;
            SuggestionProvider.CancelSuggestions();

            SuggestionProvider.GetSuggestions(TextBox_.Text);
        }

        private void Popup_Close() {
            IsPopupOpen = false;
            IsLoading = false;
        }

        private void Popup_Create(IEnumerable<int> withClasses) {
            Popup p = new Popup();
            p.PlacementTarget = Popups_[Popups_.Count - 1];
            p.Placement = PlacementMode.Left;
            p.VerticalOffset = ActualHeight - 1;
            p.HorizontalOffset = ActualWidth;
            p.Width = ActualWidth;
            p.MinHeight = 25;
            p.MaxHeight = 400;

            Border b = new Border();
            b.BorderBrush = System.Windows.Media.Brushes.Gray;
            b.BorderThickness = new Thickness(0, 1, 1, 1);
            b.Background = System.Windows.Media.Brushes.White;
            p.Child = b;

            MyListBox l = new MyListBox();
            l.ItemContainerStyle = FindResource(typeof(ListBoxItem)) as Style;
            l.ItemTemplateSelector = ItemTemplateSelector;
            l.ItemsSource = SuggestionProvider.GetSuggestions(withClasses);
            l.Focusable = false;
            l.BorderThickness = new Thickness(0);
            b.Child = l;

            p.IsOpen = true;
            Popups_.Add(p);
        }

        private void Popup_Destroy() {
            if (Popups_.Count > 1) {
                Popups_[Popups_.Count - 1].IsOpen = false;
                Popups_.RemoveAt(Popups_.Count - 1);
            }
        }

        private void Popups_Destroy() {
            while (Popups_.Count > 1) {
                Popups_[Popups_.Count - 1].IsOpen = false;
                Popups_.RemoveAt(Popups_.Count - 1);
            }
        }

        #endregion

        #region Event Handling Methods

        /// <summary>
        /// Cancel suggestion search when suggestions closed
        /// </summary>
        private void Popup_OnClosed(object sender, EventArgs e) {
            SuggestionProvider.CancelSuggestions();

            Popups_Destroy();
        }

        /// <summary>
        /// Close popup and cancel any pending search for suggestions
        /// </summary>
        private void TextBox_OnLostFocus(object sender, RoutedEventArgs e) {
            if (!IsKeyboardFocusWithin)
                Popup_Close();
        }

        /// <summary>
        /// Cancel any pending search for suggestions and initiate a new one with new value
        /// </summary>
        private void TextBox_OnTextChanged(object sender, TextChangedEventArgs e) {
            if (TextBox_.Text.Length == 0) {
                Popup_Close();
                return;
            }

            Popups_Destroy();
            Popup_Open();
        }

        /// <summary>
        /// Manage navigation in suggestions popup and run search if pressed enter
        /// </summary>
        private void TextBox_OnKeyDown(object sender, KeyEventArgs e) {
            if ((!IsPopupOpen || Selector_.SelectedItem == null) && e.Key == Key.Enter) {
                if (TextBox_.Text != string.Empty) {
                    SearchProvider?.Search(TextBox_.Text);
                    Popup_Close();
                }
                return;
            }

            // reopen suggestions if closed
            if (TextBox_.Text != string.Empty && !IsPopupOpen && (e.Key == Key.Up || e.Key == Key.Down)) {
                Popup_Open();
                return;
            }

            switch (e.Key) {
                case Key.Enter:
                case Key.Tab:
                    if (Selector_.SelectedItem != null) {
                        TextBox_.Text = ((IIdentifiable)Selector_.SelectedItem).TextRepresentation;
                        TextBox_.SelectionStart = TextBox_.Text.Length;
                        Popup_Close();
                        e.Handled = true;
                    }
                    break;
                case Key.Escape:
                    Popup_Close();
                    break;
                case Key.Up:
                    if (Selector_.SelectedIndex == -1) Selector_.SelectedIndex = Selector_.Items.Count - 1;
                    else {
                        if (Selector_.SelectedIndex == 0) Selector_.SelectedIndex = Selector_.Items.Count - 1;
                        else Selector_.SelectedIndex--;
                    }
                    ((ListBox)Selector_).ScrollIntoView(Selector_.SelectedItem);
                    break;
                case Key.Down:
                    if (Selector_.SelectedIndex == -1) Selector_.SelectedIndex = 0;
                    else {
                        if (Selector_.SelectedIndex == Selector_.Items.Count - 1) Selector_.SelectedIndex = 0;
                        else Selector_.SelectedIndex++;
                    }
                    ((ListBox)Selector_).ScrollIntoView(Selector_.SelectedItem);
                    break;
                case Key.PageUp:
                    if (Selector_.SelectedIndex != -1) {
                        int newIndex = Selector_.SelectedIndex - 5;
                        if (newIndex < 0) newIndex = 0;
                        Selector_.SelectedIndex = newIndex;
                        ((ListBox)Selector_).ScrollIntoView(Selector_.SelectedItem);
                        e.Handled = true;
                    }
                    break;
                case Key.PageDown:
                    if (Selector_.SelectedIndex != -1) {
                        int newIndex = Selector_.SelectedIndex + 5;
                        if (newIndex >= Selector_.Items.Count) newIndex = Selector_.Items.Count - 1;
                        Selector_.SelectedIndex = newIndex;
                        ((ListBox)Selector_).ScrollIntoView(Selector_.SelectedItem);
                        e.Handled = true;
                    }
                    break;
                case Key.Right:
                    if (IsPopupOpen && Selector_.SelectedItem != null) {
                        var el = ((IIdentifiable)Selector_.SelectedItem);
                        if (el.HasChildren) {
                            Popup_Create(el.Children);
                        }
                        e.Handled = true;
                    }
                    break;
                case Key.Left:
                    if (Selector_.SelectedItem != null) {
                        Popup_Destroy();
                        e.Handled = true;
                    }
                    break;
            }
        }

        #endregion

    }

    /// <summary>
    /// Type of message to be shown in Popup underneath the TextBox
    /// </summary>
    public enum SuggestionMessageType {
        /// <summary>
        /// Message is shown in <see cref="MessageBox"/> as an error of application
        /// </summary>
        Exception,
        /// <summary>
        /// Message is shown in Popup underneath the TextBox and disappears when any change to Popup occurs
        /// </summary>
        Information
    }

}
