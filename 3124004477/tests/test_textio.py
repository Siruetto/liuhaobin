"""文件输入输出模块的单元测试: 编码兼容与各类 IO 异常。"""

import os
import shutil
import tempfile
import unittest

import textio
from errors import DecodeError, InputFileError, OutputFileError


class ReadTextTest(unittest.TestCase):
    """读取: 兼容 utf-8(含 BOM) 与 gb18030, 并对失败场景给出明确异常。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _path(self, name):
        return os.path.join(self.tmpdir, name)

    def _write_bytes(self, name, payload):
        path = self._path(name)
        with open(path, "wb") as handle:
            handle.write(payload)
        return path

    def test_reads_utf8_without_bom(self):
        path = self._write_bytes("utf8.txt", "论文查重".encode("utf-8"))
        self.assertEqual("论文查重", textio.read_text(path))

    def test_reads_utf8_with_bom(self):
        path = self._write_bytes("bom.txt", "论文查重".encode("utf-8-sig"))
        self.assertEqual("论文查重", textio.read_text(path))

    def test_reads_gb18030(self):
        path = self._write_bytes("gbk.txt", "论文查重".encode("gb18030"))
        self.assertEqual("论文查重", textio.read_text(path))

    def test_missing_file_raises_input_file_error(self):
        with self.assertRaises(InputFileError):
            textio.read_text(self._path("not_exists.txt"))

    def test_directory_raises_input_file_error(self):
        with self.assertRaises(InputFileError):
            textio.read_text(self.tmpdir)

    def test_unsupported_encoding_raises_decode_error(self):
        # 0xFF 在 utf-8 与 gb18030 中都是非法字节
        path = self._write_bytes("binary.bin", b"\xff\xfe\xff\xff")
        with self.assertRaises(DecodeError):
            textio.read_text(path)


class WriteRateTest(unittest.TestCase):
    """写出: 只写小数点后两位的数字, 且目录不可用时抛出 OutputFileError。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_writes_two_decimal_number(self):
        path = os.path.join(self.tmpdir, "ans.txt")
        textio.write_rate(path, 66.66666666666667)
        with open(path, "r", encoding="utf-8") as handle:
            self.assertEqual("66.67", handle.read())

    def test_missing_directory_raises_output_file_error(self):
        path = os.path.join(self.tmpdir, "missing_dir", "ans.txt")
        with self.assertRaises(OutputFileError):
            textio.write_rate(path, 50.0)
