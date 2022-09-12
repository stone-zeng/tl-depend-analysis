MIRROR=https://mirrors.sjtug.sjtu.edu.cn/ctan

curl -o texlive.tlpdb.xz $MIRROR/systems/texlive/tlnet/tlpkg/texlive.tlpdb.xz
xz -d -f texlive.tlpdb.xz

curl -o texlive.tlpdb.sha512 $MIRROR/systems/texlive/tlnet/tlpkg/texlive.tlpdb.sha512
sha512sum -c texlive.tlpdb.sha512
rm texlive.tlpdb.sha512
