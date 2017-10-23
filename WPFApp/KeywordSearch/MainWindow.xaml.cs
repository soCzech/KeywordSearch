using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;

using CustomElements;
using KeywordSearchInterface;
using System.Globalization;

namespace KeywordSearch {

    /// <summary>
    /// Searches an index file and displays results
    /// </summary>
    public partial class MainWindow : Window {

        private string ImageFolderPath = ".\\images\\";
        private int MaxImagesOnScreen = 70;


        private ItemsControl itemsControl;
        private ContentControl notFoundMessageBox;

        public MainWindow() {
            InitializeComponent();

            var box = (SuggestionTextBox)FindName("SuggestionTextBox");
            var ksc = new KeywordSearchController(box, new string[] { ".\\GoogLeNet", ".\\YFCC100M" });

            itemsControl = (ItemsControl)FindName("ImageList");
            // add an UI element where to display errors
            notFoundMessageBox = (ContentControl)FindName("NotFoundMessageBox");

            ksc.KeywordResultsReadyEvent += OnSearchResultsReady;
            ksc.ShowSearchMessageEvent += OnShowSearchMessage;
        }

        #region Result Event Handling Methods

        private void OnSearchResultsReady(List<Filename> filenames) {
            if (itemsControl == null) {
                OnShowSearchMessage(SearchMessageType.Exception, "ImageProvider has no reference to ItemsControl.");
                return;
            }
            List<Thumbnail> thumbnails = new List<Thumbnail>();
            thumbnails.Capacity = MaxImagesOnScreen;

            int i = 0;
            foreach (var item in filenames) {
                if (i >= MaxImagesOnScreen) break;
                thumbnails.Add(new Thumbnail() { Filename = item, Image = GetImage(item.Id) });
                i++;
            }

            Application.Current.Dispatcher.BeginInvoke((Action)delegate {
                itemsControl.ItemsSource = thumbnails;
                notFoundMessageBox.Visibility = Visibility.Hidden;
            });
        }

        NotFoundMessageConverter notFoundMessageConverter = new NotFoundMessageConverter();

        /// <summary>
        /// Show error message in UI.
        /// </summary>
        /// <param name="type">Type of an error</param>
        /// <param name="message">A text the error is in</param>
        private void OnShowSearchMessage(SearchMessageType type, string message) {
            Application.Current.Dispatcher.BeginInvoke((Action)delegate {
                switch (type) {
                    case SearchMessageType.Exception:
                        MessageBox.Show(message, "Exception", MessageBoxButton.OK, MessageBoxImage.Exclamation);
                        return;
                    case SearchMessageType.NotFound:
                        notFoundMessageBox.Content = notFoundMessageConverter.Convert(message, null,
                            new string[] { "No images of ", " found" },
                            CultureInfo.CurrentCulture);
                        break;
                    case SearchMessageType.InvalidLabel:
                        notFoundMessageBox.Content = notFoundMessageConverter.Convert(message, null,
                            new string[] { "Label ", " does not exist" },
                            CultureInfo.CurrentCulture);
                        break;
                    case SearchMessageType.InvalidFormat:
                        notFoundMessageBox.Content = notFoundMessageConverter.Convert(message, null,
                            new string[] { "Input ", " is incorrectly formated" },
                            CultureInfo.CurrentCulture);
                        break;
                    case SearchMessageType.ResourcesNotLoadedYet:
                        notFoundMessageBox.Content = notFoundMessageConverter.Convert("", null,
                            new string[] { "Labels or index file not loaded yet", "" },
                            CultureInfo.CurrentCulture);
                        break;
                    default:
                        break;
                }

                notFoundMessageBox.Visibility = Visibility.Visible;
                if (itemsControl != null)
                    itemsControl.ItemsSource = null;
            });
        }

        #endregion

        private BitmapImage GetImage(uint id) {
            BitmapImage bmp = new BitmapImage();

            bmp.BeginInit();
            bmp.UriSource = new Uri(string.Format("{0}{1}.jpg", ImageFolderPath, id), UriKind.Relative);
            bmp.CacheOption = BitmapCacheOption.OnLoad;
            bmp.EndInit();
            // due to exception 'Must create DependencySource on same Thread as the DependencyObject'
            bmp.Freeze();

            return bmp;
        }

    }

    /// <summary>
    /// A struct used by ItemsControl to display images in the results.
    /// </summary>
    struct Thumbnail {
        public Filename Filename { get; set; }
        public BitmapImage Image { get; set; }
    }

}
