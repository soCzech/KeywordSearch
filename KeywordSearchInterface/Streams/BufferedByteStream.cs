using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace KeywordSearchInterface {

    /// <summary>
    /// For faster read and write of ints, floats and longs.
    /// </summary>
    class BufferedByteStream : IDisposable {

        private FileStream Stream;
        private byte[] Array = new byte[BUFFER_SIZE];
        private const int BUFFER_SIZE = 4096;
        private int BufferPointer = -1, BufferEnd = -1;
        public int Pointer { get; private set; }

        public BufferedByteStream(string filePath) {
            Pointer = 0;
            Stream = new FileStream(filePath, FileMode.Open, FileAccess.Read);
        }

        private bool ReadNextChunk() {
            BufferEnd = Stream.Read(Array, 0, BUFFER_SIZE);
            BufferPointer = 0;

            return BufferEnd != 0;
        }

        public bool IsEndOfStream() {
            if (BufferPointer == BufferEnd) {
                return !ReadNextChunk();
            }
            return false;
        }

        unsafe public Int64 ReadInt64() {
            if (BufferPointer == BufferEnd) {
                if (!ReadNextChunk())
                    throw new EndOfStreamException();
            }
            if (BufferPointer + 8 > BufferEnd) {
                    throw new FileFormatException("Invalid index file format.");
            }
            BufferPointer += 8;
            Pointer += 8;

            fixed (byte* ptr = &Array[BufferPointer - 8]) {
                return *((Int64*)ptr);
            }
        }

        unsafe public Int32 ReadInt32() {
            if (BufferPointer == BufferEnd) {
                if (!ReadNextChunk())
                    throw new EndOfStreamException();
            }
            BufferPointer += 4;
            Pointer += 4;

            fixed (byte* ptr = &Array[BufferPointer - 4]) {
                return *((Int32*)ptr);
            }
        }

        unsafe public float ReadFloat() {
            if (BufferPointer == BufferEnd) {
                if (!ReadNextChunk())
                    throw new EndOfStreamException();
            }
            BufferPointer += 4;
            Pointer += 4;

            fixed (byte* ptr = &Array[BufferPointer - 4]) {
                return *((float*)ptr);
            }
        }

        public void Dispose() {
            Stream.Close();
        }
    }

}
