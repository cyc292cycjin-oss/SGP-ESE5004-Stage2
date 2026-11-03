#!/bin/bash
# build GNU bash 4.2 locally (reviewer request: test the runner / submit scripts under bash < 4.4); source from ftp.gnu.org into a fresh folder; nothing installed system-wide
set -u
D=/home/jin/v3h/bash42; mkdir -p $D && cd $D || exit 2
[ -f bash-4.2.tar.gz ] || curl -fsSL -o bash-4.2.tar.gz https://ftp.gnu.org/gnu/bash/bash-4.2.tar.gz || { echo DOWNLOAD_FAILED; exit 3; }
sha256sum bash-4.2.tar.gz
rm -rf src && mkdir src && tar xzf bash-4.2.tar.gz -C src --strip-components=1 && cd src || exit 4
CC="gcc -std=gnu89" CFLAGS_FOR_BUILD="-std=gnu89 -Wno-implicit-function-declaration -Wno-implicit-int" CFLAGS="-O1 -std=gnu89 -Wno-implicit-function-declaration -Wno-implicit-int -Wno-int-conversion -Wno-incompatible-pointer-types -Wno-return-mismatch" ./configure --without-bash-malloc --disable-nls > ../configure.log 2>&1 || { echo CONFIGURE_FAILED; tail -5 ../configure.log; exit 5; }
make -j8 > ../make.log 2>&1 || { echo MAKE_FAILED; grep -m5 -i error ../make.log; exit 6; }
./bash --version | head -1; ./bash -c 'set -u; a=(); echo "${a[@]+"${a[@]}"}x"; echo "${a[*]:-}y"; echo "${a[@]}z"' 2>&1
