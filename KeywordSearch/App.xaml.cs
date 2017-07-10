using System;
using System.Collections.Generic;
using System.Configuration;
using System.Data;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;

namespace KeywordSearch {
    /// <summary>
    /// Interaction logic for App.xaml
    /// </summary>
    public partial class App : Application {

        private AppLogic Logic = new AppLogic();

        void MyStartup(object sender, StartupEventArgs e) {
            MainWindow window = new MainWindow(Logic);
            window.Show();
        }
    }
}
