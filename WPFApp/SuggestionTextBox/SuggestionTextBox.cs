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
        public const string PartPopup = "PART_SuggestionPopup";

        private TextBox TextBox_;
        private List<SuggestionPopup> Popups_;

        /// <summary>
        /// Initialize the UI elements and register events
        /// </summary>
        public override void OnApplyTemplate() {
            base.OnApplyTemplate();

            TextBox_ = (TextBox)Template.FindName(PartTextBox, this);
            Popups_ = new List<SuggestionPopup>();
            Popups_.Add((SuggestionPopup)Template.FindName(PartPopup, this));

            TextBox_.TextChanged += TextBox_OnTextChanged;
            TextBox_.PreviewKeyDown += TextBox_OnKeyDown;
            TextBox_.LostFocus += TextBox_OnLostFocus;

            Popups_[0].OnItemSelected += Popup_OnItemSelected;
            Popups_[0].OnItemExpanded += Popup_OnItemExpanded;
        }

        #endregion

        #region Properties

        public static readonly DependencyProperty SuggestionProviderProperty = DependencyProperty.Register("SuggestionProvider", typeof(ISuggestionProvider), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(null));
        public static readonly DependencyProperty SearchProviderProperty = DependencyProperty.Register("SearchProvider", typeof(ISearchProvider), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(null));
        public static readonly DependencyProperty ItemTemplateSelectorProperty = DependencyProperty.Register("ItemTemplateSelector", typeof(DataTemplateSelector), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(null));
        public static readonly DependencyProperty IsLoadingProperty = DependencyProperty.Register("IsLoading", typeof(bool), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(false));
        public static readonly DependencyProperty MaxNumberOfElementsProperty = DependencyProperty.Register("MaxNumberOfElements", typeof(int), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(50));
        public static readonly DependencyProperty LoadingPlaceholderProperty = DependencyProperty.Register("LoadingPlaceholder", typeof(object), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(null));

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
                if (Popups_[0].IsPopupOpen && filter == TextBox_.Text) {
                    Popups_[0].Open(MaxNumberOfElements < 0 ? suggestions : suggestions.Take(MaxNumberOfElements));
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
                        Popup_CloseAll();
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
            Popups_[0].Open(null);

            SuggestionProvider.CancelSuggestions();
            SuggestionProvider.GetSuggestions(TextBox_.Text);
        }

        private void Popup_CloseAll() {
            SuggestionProvider.CancelSuggestions();

            while (Popups_.Count > 1) {
                Popup_CloseOne();
            }
            Popup_CloseOne();
        }

        private void Popup_CloseOne() {
            Popups_[Popups_.Count - 1].Close();

            if (Popups_.Count > 1) {
                Popups_.RemoveAt(Popups_.Count - 1);
            }
        }

        #endregion

        #region Event Handling Methods

        /// <summary>
        /// Close popup and cancel any pending search for suggestions
        /// </summary>
        private void TextBox_OnLostFocus(object sender, RoutedEventArgs e) {
            if (!IsKeyboardFocusWithin)
                Popup_CloseAll();
        }

        /// <summary>
        /// Cancel any pending search for suggestions and initiate a new one with new value
        /// </summary>
        private void TextBox_OnTextChanged(object sender, TextChangedEventArgs e) {
            Popup_CloseAll();

            if (TextBox_.Text.Length != 0) {
                Popup_Open();
            }
        }

        /// <summary>
        /// Manage navigation in suggestions popup and run search if pressed enter
        /// </summary>
        private void TextBox_OnKeyDown(object sender, KeyEventArgs e) {
            if (!Popups_[0].IsPopupOpen) {
                if (e.Key == Key.Enter) {
                    SearchProvider?.Search(TextBox_.Text);
                    e.Handled = true;
                } else if ((e.Key == Key.Up || e.Key == Key.Down) && TextBox_.Text != string.Empty)  {
                    Popup_Open();
                    e.Handled = true;
                }
            } else {
                if (e.Key == Key.Escape) {
                    Popup_CloseAll();
                    e.Handled = true;
                } else if (e.Key == Key.Left) {
                    Popup_CloseOne();
                    e.Handled = true;
                } else {
                    Popups_[Popups_.Count - 1].Popup_OnKeyDown(sender, e);
                }
            }
        }

        private void Popup_OnItemSelected(object sender, SuggestionPopup.SelectedItemRoutedEventArgs e) {
            IIdentifiable item = e.SelectedItem;

            TextBox_.Text = item.TextRepresentation;
            TextBox_.SelectionStart = TextBox_.Text.Length;
            Popup_CloseAll();

            e.Handled = true;
        }

        private void Popup_OnItemExpanded(object sender, SuggestionPopup.SelectedItemRoutedEventArgs e) {
            IIdentifiable item = e.SelectedItem;
            if (!item.HasChildren) return;
            e.Handled = true;

            SuggestionPopup p = new SuggestionPopup();
            p.Open(SuggestionProvider.GetSuggestions(item.Children));
            p.ItemTemplateSelector = ItemTemplateSelector;


            p.OnItemSelected += Popup_OnItemSelected;
            p.OnItemExpanded += Popup_OnItemExpanded;
            p.PopupBorderThickness = new Thickness(0, 1, 1, 1);

            Popups_.Add(p);

            int numberOfPopups = (int)Math.Floor((System.Windows.SystemParameters.PrimaryScreenWidth - 50) / ActualWidth);
            numberOfPopups = (Popups_.Count-1) % (numberOfPopups);
            p.HorizontalOffset = ActualWidth * numberOfPopups;

            ((Grid)TextBox_.Parent).Children.Add(p);
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
