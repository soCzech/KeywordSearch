using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace ViretTool.BasicClient.Controls {
    class SuggestionTextBox : Control {

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

        public const string PartSourceStack = "PART_SourceStack";
        public const string PartResultStack = "PART_ResultStack";

        private TextBox TextBox_;
        private List<SuggestionPopup> Popups_;
        private WrapPanel RasultStack_;

        private List<QueryTextBlock> Query_ = new List<QueryTextBlock>();

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

            RasultStack_ = (WrapPanel)Template.FindName(PartResultStack, this);

            StackPanel s = (StackPanel)Template.FindName(PartSourceStack, this);
            for (int i = 0; i < AnnotationSources.Length; i++) {
                RadioButton r = new RadioButton();
                r.Tag = AnnotationSources[i];
                r.Content = AnnotationSources[i];
                r.GroupName = "AnnotationSources";
                r.Checked += AnnotationSourceButton_Checked;
                r.Margin = new Thickness(0, 0, 10, 0);
                if (i == 0) r.IsChecked = true;
                s.Children.Add(r);
            }
        }

        #endregion

        #region Properties

        public delegate void QueryChangedHandler(IEnumerable<IQueryPart> query, string annotationSource);
        public event QueryChangedHandler QueryChangedEvent;

        public delegate void SuggestionFilterChangedHandler(string filter, string annotationSource);
        public event SuggestionFilterChangedHandler SuggestionFilterChangedEvent;

        public delegate IEnumerable<IIdentifiable> GetSuggestionSubtreeHandler(IEnumerable<int> subtree, string filter, string annotationSource);
        public event GetSuggestionSubtreeHandler GetSuggestionSubtreeEvent;

        public delegate void SuggestionsNotNeededHandler();
        public event SuggestionsNotNeededHandler SuggestionsNotNeededEvent;

        public static readonly DependencyProperty AnnotationSourceProperty = DependencyProperty.Register("AnnotationSource", typeof(string), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(null));
        public static readonly DependencyProperty AnnotationSourcesProperty = DependencyProperty.Register("AnnotationSources", typeof(string[]), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(new string[0]));
        public static readonly DependencyProperty ItemTemplateSelectorProperty = DependencyProperty.Register("ItemTemplateSelector", typeof(DataTemplateSelector), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(null));
        public static readonly DependencyProperty IsLoadingProperty = DependencyProperty.Register("IsLoading", typeof(bool), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(false));
        public static readonly DependencyProperty MaxNumberOfElementsProperty = DependencyProperty.Register("MaxNumberOfElements", typeof(int), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(50));
        public static readonly DependencyProperty LoadingPlaceholderProperty = DependencyProperty.Register("LoadingPlaceholder", typeof(object), typeof(SuggestionTextBox), new FrameworkPropertyMetadata(null));

        public string AnnotationSource {
            get { return (string)GetValue(AnnotationSourceProperty); }
            set { SetValue(AnnotationSourceProperty, value); }
        }

        public string[] AnnotationSources {
            get { return (string[])GetValue(AnnotationSourcesProperty); }
            set { SetValue(AnnotationSourcesProperty, value); }
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
        public void OnShowSuggestionMessage(string message) {
            Application.Current.Dispatcher.BeginInvoke((Action)delegate {
                ((TextBlock)LoadingPlaceholder).Text = message;
            });
        }

        #endregion

        #region Control Methods

        private void Popup_Open() {
            Popups_[0].Open(null);

            SuggestionsNotNeededEvent?.Invoke();
            SuggestionFilterChangedEvent?.Invoke(TextBox_.Text, AnnotationSource);
        }

        private void Popup_CloseAll() {
            SuggestionsNotNeededEvent?.Invoke();

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
                //if (e.Key == Key.Enter) {
                //    SearchProvider?.Search(TextBox_.Text);
                //    e.Handled = true;
                //} else 
                if (e.Key == Key.Back && TextBox_.Text == string.Empty) {
                    if (Query_.Count > 0) {
                        RasultStack_.Children.Remove(Query_[Query_.Count - 1]);
                        Query_.RemoveAt(Query_.Count - 1);
                        if (Query_.Count > 0) {
                            RasultStack_.Children.Remove(Query_[Query_.Count - 1]);
                            Query_.RemoveAt(Query_.Count - 1);
                        }
                        e.Handled = true;
                        QueryChangedEvent?.Invoke(Query_, AnnotationSource);
                    }
                } else if ((e.Key == Key.Up || e.Key == Key.Down) && TextBox_.Text != string.Empty) {
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

            QueryTextBlock b = new QueryTextBlock(item, e.CtrlKeyPressed);

            if (Query_.Count > 0) {
                QueryTextBlock c = new QueryTextBlock(TextBlockType.OR);
                RasultStack_.Children.Add(c);
                Query_.Add(c);
                c.MouseUp += QueryOperator_MouseUp;
            }

            RasultStack_.Children.Add(b);
            Query_.Add(b);
            b.MouseUp += QueryClass_MouseUp;


            TextBox_.Text = string.Empty;
            //TextBox_.Text = item.TextRepresentation;
            //TextBox_.SelectionStart = TextBox_.Text.Length;
            Popup_CloseAll();

            QueryChangedEvent?.Invoke(Query_, AnnotationSource);

            e.Handled = true;
        }

        private void Popup_OnItemExpanded(object sender, SuggestionPopup.SelectedItemRoutedEventArgs e) {
            IIdentifiable item = e.SelectedItem;
            if (!item.HasChildren) return;
            e.Handled = true;

            SuggestionPopup p = new SuggestionPopup();
            p.Open(GetSuggestionSubtreeEvent?.Invoke(item.Children, TextBox_.Text, AnnotationSource));
            p.ItemTemplateSelector = ItemTemplateSelector;


            p.OnItemSelected += Popup_OnItemSelected;
            p.OnItemExpanded += Popup_OnItemExpanded;
            p.PopupBorderThickness = new Thickness(0, 1, 1, 1);

            Popups_.Add(p);

            int numberOfPopups = (int)Math.Floor((System.Windows.SystemParameters.PrimaryScreenWidth - 50) / ActualWidth);
            numberOfPopups = (Popups_.Count - 1) % (numberOfPopups);
            p.HorizontalOffset = ActualWidth * numberOfPopups;

            ((Grid)TextBox_.Parent).Children.Add(p);
        }

        private void AnnotationSourceButton_Checked(object sender, RoutedEventArgs e) {
            RadioButton rb = sender as RadioButton;
            if (rb == null) return;

            ClearQuery();

            AnnotationSource = rb.Tag.ToString();
        }

        #endregion
        
        public void ClearQuery() {
            RasultStack_.Children.Clear();
            Query_.Clear();
            QueryChangedEvent?.Invoke(Query_, AnnotationSource);
        }

        private void QueryClass_MouseUp(object sender, MouseButtonEventArgs e) {
            QueryTextBlock b = sender as QueryTextBlock;

            for (int i = 0; i < Query_.Count; i++) {
                if (Query_[i].Id == b.Id) {
                    if (i + 1 != Query_.Count) {
                        RasultStack_.Children.Remove(Query_[i + 1]);
                        Query_.RemoveAt(i + 1);
                    }
                    RasultStack_.Children.Remove(Query_[i]);
                    Query_.RemoveAt(i);

                    if (i != 0 && i == Query_.Count) {
                        RasultStack_.Children.Remove(Query_[i - 1]);
                        Query_.RemoveAt(i - 1);
                    }
                    break;
                }
            }

            QueryChangedEvent?.Invoke(Query_, AnnotationSource);
        }

        private void QueryOperator_MouseUp(object sender, MouseButtonEventArgs e) {
            QueryTextBlock b = sender as QueryTextBlock;

            b.Type = b.Type == TextBlockType.AND ? TextBlockType.OR : TextBlockType.AND;
            b.Text = b.Type == TextBlockType.AND ? "AND" : "OR";

            QueryChangedEvent?.Invoke(Query_, AnnotationSource);
        }
    }

}
