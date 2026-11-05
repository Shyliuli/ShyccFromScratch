# exp0：环境配置

这一节不写编译器，只把工具链装好：能用 ShyCC 编译 C 程序，并分别在 ShyEmu 和本机上运行。

## 1. 获取 ShyProject

ShyProject 里有 ShyCC（编译器）、ShyEmu（模拟器）和 libshy（标准库）。

```sh
git clone https://github.com/Shyliuli/ShyProject.git
cd ShyProject
```

## 2. 安装依赖

- **Rust**：用来编译 ShyCC 和 ShyEmu。没装的话用 [rustup](https://rustup.rs)：

  ```sh
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  ```

- **clang**：ShyCC 默认编译到 ShyISA，不需要 clang；编译到本机（`--target host`）时由 clang 生成代码并链接。

  ```sh
  sudo pacman -S clang      # Arch
  sudo apt install clang    # Debian / Ubuntu
  ```

- **Python 3**：用来运行 `exam/exam.py`。

## 3. 编译并安装 ShyCC 和 ShyEmu

在 ShyProject 目录下：

```sh
make install-bin PREFIX=~/.local
```

这条命令会做两件事：

- 编译工具链并安装到 `~/.local/bin`：`shycc`（编译驱动）、`shyc`（C/ShyC 编译器）、`shyasm`（汇编器）、`shyld`（链接器）、`shyemu`（模拟器）；
- 生成 `~/.shycc.toml`，记录 libshy 的位置，这样在任何目录下都能编译。

确认 `~/.local/bin` 在 `PATH` 里：

```sh
shycc --version
shyc --version
shyasm --version
shyld --version
shyemu --version
```

如果提示找不到命令，把 `export PATH="$HOME/.local/bin:$PATH"` 加到 `~/.bashrc`（或你用的 shell 的配置文件）里，然后重开终端。

## 4. 编译运行第一个程序

回到本仓库（ShyccFromScratch）目录：

```sh
# 编译到 ShyISA，用 ShyEmu 运行
shycc ./playground/hello.c -o hello.sfs
shyemu ./hello.sfs

# 编译到本机，直接运行
shycc --target host ./playground/hello.c -o hello.elf
./hello.elf
```

两次都应该输出 `hello world`。

## exam

```sh
python3 exam/exam.py
```

它会检查 `shycc`、`shyc`、`shyasm`、`shyld`、`shyemu`、`clang` 的 `--version` 能否运行，再用上面两种方式编译运行 `exam/hello.c`，核对输出。全部通过，exp0 就完成了。
