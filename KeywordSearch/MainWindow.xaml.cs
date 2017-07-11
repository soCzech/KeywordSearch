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

            var Box = (SuggestionTextBox)FindName("SuggestionTextBox");
            Box.SuggestionProvider = Logic.SuggestionProvider;
            Box.SearchProvider = Logic.ImageProvider;

            //Logic.ImageProvider.ViewModel1();
            var x = (ItemsControl)FindName("imageList");
            //x.ItemsSource = Logic.ImageProvider.Products;
        }
    }
}
