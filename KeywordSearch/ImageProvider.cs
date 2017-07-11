using CustomElements;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Media.Imaging;

namespace KeywordSearch {

    class Product {
        public string Path { get; set; }
        public BitmapImage Image { get; set; }

        public Product(string path, BitmapImage image) {
            Path = path;
            Image = image;
        }
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

        private BitmapImage GetImage(string path) {
            BitmapImage bmp = new BitmapImage();

            bmp.BeginInit();
            bmp.UriSource = new Uri(path, UriKind.Relative);
            bmp.CacheOption = BitmapCacheOption.OnLoad;
            bmp.EndInit();

            return bmp;
        }

        public void Search(string filter) {
            throw new NotImplementedException();
        }
    }
}
