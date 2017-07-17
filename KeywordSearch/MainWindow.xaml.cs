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

using CustomElements;

namespace KeywordSearch {
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window {
        private AppLogic Logic;

        public MainWindow(AppLogic logic) {
            Logic = logic;

            InitializeComponent();

            // add SuggestionProvider and SearchProvider to the search box
            var Box = (SuggestionTextBox)FindName("SuggestionTextBox");
            Box.SuggestionProvider = Logic.SuggestionProvider;
            Box.SearchProvider = Logic.ImageProvider;

            // add an UI element where to display the results
            Logic.ImageProvider.ItemsControl = (ItemsControl)FindName("ImageList");
            // add an UI element where to display errors
            Logic.ImageProvider.NotFoundMessageBox = (ContentControl)FindName("NotFoundMessageBox");
        }
    }
}
