using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ViretTool.RankingModel;
using System.Windows.Media.Imaging;

namespace ViretTool {
    /// <summary>
    /// A struct used by ItemsControl to display images in the results.
    /// </summary>
    struct Thumbnail {
        public Frame Frame { get; set; }
        public BitmapImage Image { get; set; }

        public Thumbnail(Frame frame, string path) {
            Frame = frame;

            Image = new BitmapImage();

            Image.BeginInit();
            Image.UriSource = new Uri(string.Format("{0}/{1}.jpg", path, frame.Id.ToString("D7")), UriKind.Relative);
            Image.CacheOption = BitmapCacheOption.OnLoad;
            Image.EndInit();
            Image.Freeze();
        }
    }
}
