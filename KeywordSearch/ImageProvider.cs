using CustomElements;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media.Imaging;
using KeywordSearchInterface;
using System.Windows.Threading;

namespace KeywordSearch {

    /// <summary>
    /// A struct used by ItemsControl to display images in the results.
    /// </summary>
    struct Thumbnail {
        public Filename Filename { get; set; }
        public BitmapImage Image { get; set; }
    }

    /// <summary>
    /// Searches an index file and displays results
    /// </summary>
    class WPFImageProvider {
        internal LabelProvider LabelProvider;
        internal SuggestionProvider SuggestionProvider;
        internal ImageProvider ImageProvider;

        public ItemsControl ItemsControl { get; set; }
        public ContentControl NotFoundMessageBox { get; set; }

        public WPFImageProvider(SuggestionTextBox box, ItemsControl imageList, ContentControl notFoundMessageBox) {
            LabelProvider = new LabelProvider();
            SuggestionProvider = new SuggestionProvider(LabelProvider);
            ImageProvider = new ImageProvider(LabelProvider);


            // add SuggestionProvider and SearchProvider to the search box
            box.SuggestionProvider = SuggestionProvider;
            box.SearchProvider = ImageProvider;
            // add an UI element where to display the results
            ItemsControl = imageList;
            // add an UI element where to display errors
            NotFoundMessageBox = notFoundMessageBox;

            ImageProvider.SearchErrorEvent += ShowNotFoundMessageBox;
            ImageProvider.SearchResultsReadyEvent += ImageProvider_SearchResultsReadyEvent;

            SuggestionProvider.SearchErrorEvent += box.OnSearchErrorEvent;
            SuggestionProvider.SuggestionResultsReadyEvent += box.OnSuggestionUpdate;
        }

        private void ImageProvider_SearchResultsReadyEvent(List<Filename> filenames) {
            if (ItemsControl == null) {
                ShowNotFoundMessageBox(ErrorMessageType.Exception, "ImageProvider has no reference to ItemsControl.");
                return;
            }
            List<Thumbnail> thumbnails = new List<Thumbnail>();
            foreach (var item in filenames) {
                thumbnails.Add(new Thumbnail() { Filename = item, Image = GetImage(item.Id) });
            }

            Application.Current.Dispatcher.BeginInvoke((Action)delegate {
                ItemsControl.ItemsSource = thumbnails;
                HideNotFoundMessageBox();
            });
        }

        private string ImageFolderPath = ".\\images\\";

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
        
        NotFoundMessageConverter NotFoundMessageConverter = new NotFoundMessageConverter();

        /// <summary>
        /// Show error message in UI.
        /// </summary>
        /// <param name="type">Type of an error</param>
        /// <param name="message">A text the error is in</param>
        private void ShowNotFoundMessageBox(ErrorMessageType type, string message) {
            Application.Current.Dispatcher.BeginInvoke((Action)delegate {
                switch (type) {
                    case ErrorMessageType.Exception:
                        MessageBox.Show(message, "Exception", MessageBoxButton.OK, MessageBoxImage.Exclamation);
                        return;
                    case ErrorMessageType.NotFound:
                        NotFoundMessageBox.Content = NotFoundMessageConverter.Convert(message, null,
                            new string[] { "No images of ", " found" },
                            CultureInfo.CurrentCulture);
                        break;
                    case ErrorMessageType.InvalidLabel:
                        NotFoundMessageBox.Content = NotFoundMessageConverter.Convert(message, null,
                            new string[] { "Label ", " does not exist" },
                            CultureInfo.CurrentCulture);
                        break;
                    case ErrorMessageType.InvalidFormat:
                        NotFoundMessageBox.Content = NotFoundMessageConverter.Convert(message, null,
                            new string[] { "Input ", " is incorrectly formated" },
                            CultureInfo.CurrentCulture);
                        break;
                    case ErrorMessageType.ResourcesNotLoadedYet:
                        NotFoundMessageBox.Content = NotFoundMessageConverter.Convert("", null,
                            new string[] { "Labels or index file not loaded yet", "" },
                            CultureInfo.CurrentCulture);
                        break;
                    default:
                        break;
                }

                NotFoundMessageBox.Visibility = Visibility.Visible;
                if (ItemsControl != null)
                    ItemsControl.ItemsSource = null;
            });
        }

        private void HideNotFoundMessageBox() {
            NotFoundMessageBox.Visibility = Visibility.Hidden;
        }
    }
}
