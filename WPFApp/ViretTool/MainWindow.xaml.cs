using System;
using System.Collections.Generic;
using System.IO;
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
using ViretTool.RankingModel.SimilarityModels;

namespace ViretTool {
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window {
        const int MaxImagesOnScreen = 70;

        string imagePath;
        KeywordModelWrapper model;

        public MainWindow() {
            InitializeComponent();

            string[] sourceNames, indexFiles, idfFiles, labelFiles;
            LoadFromConfig(out sourceNames, out indexFiles, out idfFiles, out labelFiles);

            model = new KeywordModelWrapper(indexFiles, idfFiles, sourceNames);

            keywordSearchTextBox.Init(labelFiles, sourceNames);
            keywordSearchTextBox.KeywordChangedEvent += KeywordSearchTextBox_KeywordChangedEvent;
        }

        /// <summary>
        /// Query changed handler, calls model ranking and than displays results
        /// </summary>
        private void KeywordSearchTextBox_KeywordChangedEvent(List<List<int>> query, string annotationSource) {
            var result = model.RankFramesBasedOnQuery(query, annotationSource);
             
            // show message in the center of the window if no result present
            if (result == null) {
                imageList.ItemsSource = null;
                notFoundMessageBox.Text = "Type a query";
                notFoundMessageBox.Visibility = Visibility.Visible;
                return;
            } else if (result.Count == 0) {
                imageList.ItemsSource = null;
                notFoundMessageBox.Text = "Nothing found";
                notFoundMessageBox.Visibility = Visibility.Visible;
                return;
            }

            List<Thumbnail> thumbnails = new List<Thumbnail>(MaxImagesOnScreen);

            // show images to user
            int i = 0;
            foreach (var item in result) {
                if (i >= MaxImagesOnScreen) break;
                thumbnails.Add(new Thumbnail(item, imagePath));
                i++;
            }

            imageList.ItemsSource = thumbnails;
            notFoundMessageBox.Visibility = Visibility.Hidden;
        }

        /// <summary>
        /// Loads settings from config file
        /// </summary>
        private void LoadFromConfig(out string[] sourceNames, out string[] indexFiles, out string[] idfFiles, out string[] labelFiles) {
            var file = Directory.GetFiles(".", "*.ini");
            if (file.Length != 1) {
                throw new Exception("Exactly one *.ini file must be in the directory where the application is located.");
            }

            imagePath = "./images/"; // default value if nothing in the ini file
            var srcnames = new List<string>();
            var idxfiles = new List<string>();
            var idffiles = new List<string>();
            var lblfiles = new List<string>();

            using (StreamReader reader = new StreamReader(file[0])) {
                string source = null;
                string index = null;
                string idf = null;
                string label = null;

                while (!reader.EndOfStream) {
                    var line = reader.ReadLine();
                    if (line.Length == 0) continue;

                    if (line[0] == '[') {
                        if (source != null) {
                            if (label == null || index == null) {
                                throw new Exception("Incomplete definition of a source in *.ini file.");
                            }
                            srcnames.Add(source);
                            idxfiles.Add(index);
                            idffiles.Add(idf);
                            lblfiles.Add(label);
                            index = null;
                            idf = null;
                            label = null;
                        }
                        source = String.Concat(line.Skip(1).Take(line.Length - 2));
                        continue;
                    }
                    var parts = line.Split('=');
                    switch (parts[0]) {
                        case "images":
                            imagePath = parts[1];
                            break;
                        case "label":
                            label = parts[1];
                            break;
                        case "index":
                            index = parts[1];
                            break;
                        case "idf":
                            idf = parts[1];
                            break;
                        default:
                            throw new Exception("Unsupported line in *.ini file.");
                    }
                }

                if (source != null) {
                    if (label == null || index == null) {
                        throw new Exception("Incomplete definition of a source in *.ini file.");
                    }
                    srcnames.Add(source);
                    idxfiles.Add(index);
                    idffiles.Add(idf);
                    lblfiles.Add(label);
                }
            }
            sourceNames = srcnames.ToArray();
            indexFiles = idxfiles.ToArray();
            idfFiles = idffiles.ToArray();
            labelFiles = lblfiles.ToArray();
        }

    }
}
