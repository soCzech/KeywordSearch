using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;

namespace CustomElements {

    public class SuggestionPopup : Control {

        static SuggestionPopup() {
            DefaultStyleKeyProperty.OverrideMetadata(typeof(SuggestionPopup), new FrameworkPropertyMetadata(typeof(SuggestionPopup)));
        }

        #region Initialization

        /// <summary>
        /// Indetifies Popup (containing list of suggestions) part of the UI element
        /// </summary>
        public const string PartPopup = "PART_Popup";
        /// <summary>
        /// Indetifies ListBox (with suggestions) part of the UI element
        /// </summary>
        public const string PartListBox = "PART_ListBox";

        private Popup mPopup;
        private ListBox mListBox;

        /// <summary>
        /// Initialize the UI elements and register events
        /// </summary>
        public override void OnApplyTemplate() {
            base.OnApplyTemplate();
            mPopup = (Popup)Template.FindName(PartPopup, this);
            mListBox = (ListBox)Template.FindName(PartListBox, this);

            mListBox.SelectedIndex = 0;

            mPopup.StaysOpen = false;
        }

        #endregion

        #region Properties

        public delegate void SelectedItemRoutedEventHandler(object sender, SelectedItemRoutedEventArgs e);
        public class SelectedItemRoutedEventArgs : RoutedEventArgs {
            public SelectedItemRoutedEventArgs(RoutedEvent e, IIdentifiable item) : base(e) {
                SelectedItem = item;
            }
            public IIdentifiable SelectedItem { get; private set; }
        }
        public static readonly RoutedEvent OnItemSelectedEvent = EventManager.RegisterRoutedEvent("OnItemSelected", RoutingStrategy.Bubble, typeof(SelectedItemRoutedEventHandler), typeof(SuggestionPopup));

        public event SelectedItemRoutedEventHandler OnItemSelected {
            add { AddHandler(OnItemSelectedEvent, value); }
            remove { RemoveHandler(OnItemSelectedEvent, value); }
        }
        public static readonly RoutedEvent OnItemExpandedEvent = EventManager.RegisterRoutedEvent("OnItemExpanded", RoutingStrategy.Bubble, typeof(SelectedItemRoutedEventHandler), typeof(SuggestionPopup));

        public event SelectedItemRoutedEventHandler OnItemExpanded {
            add { AddHandler(OnItemExpandedEvent, value); }
            remove { RemoveHandler(OnItemExpandedEvent, value); }
        }
        public static readonly DependencyProperty ItemsSourceProperty = DependencyProperty.Register("ItemsSource", typeof(IEnumerable<IIdentifiable>), typeof(SuggestionPopup), new FrameworkPropertyMetadata(null));
        public static readonly DependencyProperty IsPopupOpenProperty = DependencyProperty.Register("IsPopupOpen", typeof(bool), typeof(SuggestionPopup), new FrameworkPropertyMetadata(false));
        public static readonly DependencyProperty ItemTemplateSelectorProperty = DependencyProperty.Register("ItemTemplateSelector", typeof(DataTemplateSelector), typeof(SuggestionPopup), new FrameworkPropertyMetadata(null));
        public static readonly DependencyProperty IsLoadingProperty = DependencyProperty.Register("IsLoading", typeof(bool), typeof(SuggestionPopup), new FrameworkPropertyMetadata(false));
        public static readonly DependencyProperty MaxNumberOfElementsProperty = DependencyProperty.Register("MaxNumberOfElements", typeof(int), typeof(SuggestionPopup), new FrameworkPropertyMetadata(50));
        public static readonly DependencyProperty LoadingPlaceholderProperty = DependencyProperty.Register("LoadingPlaceholder", typeof(object), typeof(SuggestionPopup), new FrameworkPropertyMetadata(null));


        public IEnumerable<IIdentifiable> ItemsSource {
            get { return (IEnumerable<IIdentifiable>)GetValue(ItemsSourceProperty); }
            private set { SetValue(ItemsSourceProperty, value); }
        }

        /// <summary>
        /// Indicates if the suggestions popup is open.
        /// </summary>
        public bool IsPopupOpen {
            get { return (bool)GetValue(IsPopupOpenProperty); }
            private set { SetValue(IsPopupOpenProperty, value); }
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
            private set { SetValue(IsLoadingProperty, value); }
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


        /// <summary>
        /// Manage navigation in suggestions popup and run search if pressed enter
        /// </summary>
        public void Popup_OnKeyDown(object sender, KeyEventArgs e) {
            if (!IsPopupOpen) {
                throw new Exception();
            }
            if (IsLoading) return;

            switch (e.Key) {
                case Key.Enter:
                case Key.Tab:
                    if (mListBox.SelectedItem != null) {
                        RaiseEvent(new RoutedEventArgs(OnItemSelectedEvent, mListBox.SelectedItem));
                        e.Handled = true;
                    }
                    break;

                case Key.Up:
                    if (mListBox.SelectedIndex == -1) mListBox.SelectedIndex = mListBox.Items.Count - 1;
                    else {
                        if (mListBox.SelectedIndex == 0) mListBox.SelectedIndex = mListBox.Items.Count - 1;
                        else mListBox.SelectedIndex--;
                    }
                    mListBox.ScrollIntoView(mListBox.SelectedItem);
                    e.Handled = true;
                    break;

                case Key.Down:
                    if (mListBox.SelectedIndex == -1) mListBox.SelectedIndex = 0;
                    else {
                        if (mListBox.SelectedIndex == mListBox.Items.Count - 1) mListBox.SelectedIndex = 0;
                        else mListBox.SelectedIndex++;
                    }
                    mListBox.ScrollIntoView(mListBox.SelectedItem);
                    e.Handled = true;
                    break;

                case Key.PageUp:
                    if (mListBox.SelectedIndex != -1) {
                        int newIndex = mListBox.SelectedIndex - 5;
                        if (newIndex < 0) newIndex = 0;
                        mListBox.SelectedIndex = newIndex;
                        mListBox.ScrollIntoView(mListBox.SelectedItem);
                    }
                    e.Handled = true;
                    break;

                case Key.PageDown:
                    if (mListBox.SelectedIndex != -1) {
                        int newIndex = mListBox.SelectedIndex + 5;
                        if (newIndex >= mListBox.Items.Count) newIndex = mListBox.Items.Count - 1;
                        mListBox.SelectedIndex = newIndex;
                        mListBox.ScrollIntoView(mListBox.SelectedItem);
                    }
                    e.Handled = true;
                    break;

                case Key.Left:
                    if (mListBox.SelectedItem != null) {
                        RaiseEvent(new RoutedEventArgs(OnItemExpandedEvent, mListBox.SelectedItem));
                        e.Handled = true;
                    }
                    break;
            }
        }

        public void Close() {
            IsPopupOpen = false;
            IsLoading = false;
            ItemsSource = null;
        }

        public void Open(IEnumerable<IIdentifiable> e) {
            IsPopupOpen = true;

            if (e != null) {
                if (e.Any()) {
                    ItemsSource = e;
                    mListBox.SelectedIndex = 0;
                    IsLoading = false;
                } else {
                    Close();
                }
            } else {
                IsLoading = true;
                ItemsSource = null;
            }
        }
    }
}
