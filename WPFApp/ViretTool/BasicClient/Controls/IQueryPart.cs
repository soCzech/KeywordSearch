using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ViretTool.BasicClient.Controls {
    public interface IQueryPart {
        int Id { get; }
        bool UseChildren { get; }
        TextBlockType Type { get; }
    }
    public enum TextBlockType { Class, OR, AND }
}
