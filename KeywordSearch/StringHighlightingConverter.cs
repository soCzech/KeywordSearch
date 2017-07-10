// http://underground.infovark.com/2011/03/03/highlighting-query-terms-in-a-wpf-textblock/

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Data;
using System.Windows.Markup;
using System.Xml;

namespace KeywordSearch {

    [ValueConversion(typeof(string), typeof(object))]
    sealed class StringHighlightingConverter : IValueConverter {
        public const string START_TAG = "$~START~$";
        public const string END_TAG = "$~END~$";

        public object Convert(object value, Type targetType, object parameter, CultureInfo culture) {
            string input = value as string;
            if (input == null) return null;

            string escaped = SecurityElement.Escape(input);
            string xml = escaped.Replace(START_TAG, "<Run Style=\"{DynamicResource ResourceKey=highlightedText}\">").Replace(END_TAG, "</Run>");

            string wrappedXml = string.Format("<TextBlock xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\" xml:space=\"preserve\" TextWrapping=\"Wrap\">{0}</TextBlock>", xml);

            using (StringReader stringReader = new StringReader(wrappedXml)) {
                using (XmlReader xmlReader = XmlReader.Create(stringReader)) {
                    return XamlReader.Load(xmlReader);
                }
            }
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) {
            throw new NotImplementedException("The converter does not support two-way binding.");
        }
    }
}
