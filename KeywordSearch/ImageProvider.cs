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

namespace KeywordSearch {

    struct Thumbnail {
        public Filename Filename { get; set; }
        public BitmapImage Image { get; set; }
    }

    struct Filename {
        public uint Id { get; set; }
        public float Probability { get; set; }
    }

    class ImageProvider : ISearchProvider {

        private string IndexFilePath = ".\\files.index";
        private string ImageFolderPath = ".\\images\\";

        public ImageProvider(LabelProvider lp) {
            LabelProvider = lp;
            LoadTask = Task.Factory.StartNew(LoadFromFile);
        }

        public ImageProvider(LabelProvider lp, string filePath, string folderPath) {
            LabelProvider = lp;

            IndexFilePath = filePath;
            ImageFolderPath = folderPath;

            LoadTask = Task.Factory.StartNew(LoadFromFile);
        }

        private LabelProvider LabelProvider;
        private Dictionary<int, List<Filename>> Classes = new Dictionary<int, List<Filename>>();
        private Task LoadTask { get; set; }
        public ItemsControl ItemsControl { get; set; }
        public ContentControl NotFoundMessageBox { get; set; }

        private void LoadFromFile() {
            BufferedByteStream stream = null;
            Dictionary<int, int> classLocations = new Dictionary<int, int>();

            try {
                stream = new BufferedByteStream(IndexFilePath);

                if (stream.ReadInt64() != 0x4b5320494e444558 && stream.ReadInt64() != -1)
                    throw new FileFormatException("Invalid index file format.");
                
                while (true) {
                    int value = stream.ReadInt32();
                    int valueOffset = stream.ReadInt32();

                    if (value != -1) {
                        classLocations.Add(valueOffset, value);
                    } else break;
                }

                while (true) {
                    if (stream.IsEndOfStream()) break;

                    if (!classLocations.ContainsKey(stream.Pointer))
                        throw new FileFormatException("Invalid index file format.");

                    int classId = classLocations[stream.Pointer];
                    Classes.Add(classId, new List<Filename>());

                    while (true) {
                        uint imageId = (uint)stream.ReadInt32();
                        float imageProbability = stream.ReadFloat();

                        if (imageId != 0xffffffff) {
                            Classes[classId].Add(new Filename() { Id = imageId, Probability = imageProbability });
                        } else break;
                    }
                }
            } finally {
                stream.Dispose();
            }
        }

        private BitmapImage GetImage(uint id) {
            BitmapImage bmp = new BitmapImage();

            bmp.BeginInit();
            bmp.UriSource = new Uri(string.Format("{0}{1}.jpg", ImageFolderPath, id), UriKind.Relative);
            bmp.CacheOption = BitmapCacheOption.OnLoad;
            bmp.EndInit();

            return bmp;
        }

        public void Search(string filter, SuggestionTextBox suggestionTextBox) {
            if (LabelProvider.LoadTask.IsFaulted) {
                suggestionTextBox.Dispatcher.BeginInvoke(new Action(
                    () => { MessageBox.Show(LabelProvider.LoadTask.Exception.InnerException.Message, "Exception", MessageBoxButton.OK, MessageBoxImage.Exclamation); }
                    ));
                return;
            } else if (LoadTask.IsFaulted) {
                suggestionTextBox.Dispatcher.BeginInvoke(new Action(
                    () => { MessageBox.Show(LoadTask.Exception.InnerException.Message, "Exception", MessageBoxButton.OK, MessageBoxImage.Exclamation); }
                    ));
                return;
            } else if (!LabelProvider.LoadTask.IsCompleted || !LoadTask.IsCompleted) {
                ShowNotFoundMessageBox(null);
                return;
            }

            Label label = null;
            if (LabelProvider.Labels.TryGetValue(filter, out label) && Classes.ContainsKey(label.Id)) {
                List<Filename> list = Classes[label.Id];
                List<Thumbnail> thumbnails = new List<Thumbnail>();

                foreach (var item in list) {
                    thumbnails.Add(new Thumbnail() { Filename = item, Image = GetImage(item.Id) });
                }
                if (ItemsControl != null) {
                    ItemsControl.ItemsSource = thumbnails;
                    HideNotFoundMessageBox();
                } else {
                    suggestionTextBox.Dispatcher.BeginInvoke(new Action(
                        () => { MessageBox.Show("ImageProvider has no reference to ItemsControl.", "Error", MessageBoxButton.OK, MessageBoxImage.Exclamation); }
                        ));
                }
            } else {
                ShowNotFoundMessageBox(filter);
                if (ItemsControl != null)
                    ItemsControl.ItemsSource = null;
                return;
            }
        }

        enum NotFoundMessageType { NotFound, NotValidClass }
        NotFoundMessageConverter NotFoundMessageConverter = new NotFoundMessageConverter();

        private void ShowNotFoundMessageBox(string message) {
            NotFoundMessageBox.Content = NotFoundMessageConverter.Convert(message, null, null, CultureInfo.CurrentCulture);
            NotFoundMessageBox.Visibility = Visibility.Visible;
        }
        private void HideNotFoundMessageBox() {
            NotFoundMessageBox.Visibility = Visibility.Hidden;
        }
    }
}
