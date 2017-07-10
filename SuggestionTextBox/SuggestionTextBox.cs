// https://wpfautocomplete.codeplex.com/

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using System.Windows.Controls.Primitives;

using System.Diagnostics;
using System.Collections;

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
    ///     <MyNamespace:SuggestionTextBox/>
    ///
    /// </summary>
    public class SuggestionTextBox : Control {

        static SuggestionTextBox() {
            DefaultStyleKeyProperty.OverrideMetadata(typeof(SuggestionTextBox), new FrameworkPropertyMetadata(typeof(SuggestionTextBox)));
        }

        public const string PartTextBox = "PART_TextBox";
        public const string PartPopup = "PART_Popup";
        public const string PartListBox = "PART_ListBox";

        public static readonly DependencyProperty IsPopupOpenProperty = DependencyProperty.Register("IsPopupOpen", typeof(bool), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(false));
        public static readonly DependencyProperty SuggestionProviderProperty = DependencyProperty.Register("SuggestionProvider", typeof(ISuggestionProvider), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(null));
        public static readonly DependencyProperty ItemTemplateProperty = DependencyProperty.Register("ItemTemplate", typeof(DataTemplate), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(null));
        public static readonly DependencyProperty IsLoadingProperty = DependencyProperty.Register("IsLoading", typeof(bool), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(false));
        public static readonly DependencyProperty LoadingPlaceholderProperty = DependencyProperty.Register("LoadingPlaceholder", typeof(object), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(null));

        public bool IsPopupOpen {
            get { return (bool)GetValue(IsPopupOpenProperty); }
            set { SetValue(IsPopupOpenProperty, value); }
        }
        public ISuggestionProvider SuggestionProvider {
            get { return (ISuggestionProvider)GetValue(SuggestionProviderProperty); }
            set { SetValue(SuggestionProviderProperty, value); }
        }
        public DataTemplate ItemTemplate {
            get { return (DataTemplate)GetValue(ItemTemplateProperty); }
            set { SetValue(ItemTemplateProperty, value); }
        }
        public bool IsLoading {
            get { return (bool)GetValue(IsLoadingProperty); }
            set { SetValue(IsLoadingProperty, value); }
        }
        public object LoadingPlaceholder {
            get { return GetValue(LoadingPlaceholderProperty); }
            set { SetValue(LoadingPlaceholderProperty, value); }
        }

        private TextBox TextBox_;
        private Popup Popup_;
        private Selector Selector_;

        public override void OnApplyTemplate() {
            base.OnApplyTemplate();

            TextBox_ = (TextBox)Template.FindName(PartTextBox, this);
            Popup_ = (Popup)Template.FindName(PartPopup, this);
            Selector_ = (Selector)Template.FindName(PartListBox, this);

            TextBox_.TextChanged += TextBox_OnTextChanged;
            TextBox_.PreviewKeyDown += TextBox_OnKeyDown;
            TextBox_.LostFocus += TextBox_OnLostFocus;

            Popup_.StaysOpen = false;
            Popup_.Closed += Popup_OnClosed;
        }

        private void TextBox_OnLostFocus(object sender, RoutedEventArgs e) {
            if (!IsKeyboardFocusWithin)
                Popup_Close();
        }

        private void TextBox_OnTextChanged(object sender, TextChangedEventArgs e) {
            if (TextBox_.Text.Length == 0) {
                Popup_Close();
                return;
            }

            Popup_Open();
        }

        private void TextBox_OnKeyDown(object sender, KeyEventArgs e) {
            if (Selector_.SelectedItem == null && e.Key == Key.Enter) {
                //SearchHandler?.Invoke(TextBox_.Text);
                return;
            }

            if (TextBox_.Text != string.Empty && !IsPopupOpen && (e.Key == Key.Up || e.Key == Key.Down)) {
                Popup_Open();
                return;
            }

            switch (e.Key) {
                case Key.Enter:
                    TextBox_.Text = ((IIdentifiable)Selector_.SelectedItem).GetTextRepresentation();
                    TextBox_.SelectionStart = TextBox_.Text.Length;
                    Popup_Close();
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
                //case Key.PageUp:
                //    break;
                //case Key.PageDown:
                //    break;
            }
        }

        private void Popup_Open() {
            IsPopupOpen = true;
            IsLoading = true;

            Selector_.ItemsSource = null;
            SuggestionProvider.CancelSuggestionsLookup();

            SuggestionProvider.GetSuggestionsAsync(TextBox_.Text, this);
        }

        private void Popup_Close() {
            IsPopupOpen = false;
            IsLoading = false;
        }

        private void Popup_OnClosed(object sender, EventArgs e) {
            SuggestionProvider.CancelSuggestionsLookup();
        }

        public void OnSuggestionUpdate(IEnumerable<IIdentifiable> suggestions, string filter) {
            if (IsPopupOpen && filter == TextBox_.Text) {
                IsLoading = false;
                Selector_.ItemsSource = suggestions;
                IsPopupOpen = Selector_.HasItems;
            }
        }

    }
}
