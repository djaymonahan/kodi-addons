#!/bin/sh
################################################################################
#      This file is part of Alex@ELEC - http://www.alexelec.in.ua
#      Copyright (C) 2011-2017 Alexandr Zuyev (alex@alexelec.in.ua)
################################################################################

################################################################################
# Colors
ESC_SEQ="\x1b["
COL_RESET=$ESC_SEQ"39;49;00m"
COL_RED=$ESC_SEQ"31;01m"
COL_GREEN=$ESC_SEQ"32;01m"
COL_YELLOW=$ESC_SEQ"33;01m"
COL_BLUE=$ESC_SEQ"34;01m"
COL_MAGENTA=$ESC_SEQ"35;01m"
COL_CYAN=$ESC_SEQ"36;01m"
################################################################################

ADDON_LIST="script.torrent-tv.aml \
            script.module.torrent.ts \
            script.module.xbmcup \
            plugin.video.zona.mobi"

REPO_DIR="repo"
PY_GEN="generator.py"

echo -e "${COL_YELLOW}Creating repository...${COL_RESET}"
echo ""
mkdir -p $REPO_DIR
rm -fr $REPO_DIR/*

for addon in $ADDON_LIST; do
  echo -e "${COL_BLUE}copy addon:${COL_CYAN} $addon${COL_RESET}"
  cp -a $addon $REPO_DIR
done
cp $PY_GEN $REPO_DIR

echo ""
echo -e "Generates a new addons.xml and a new addons.xml.md5..."
pushd $REPO_DIR > /dev/null

python $PY_GEN
rm -f $PY_GEN
echo ""

for addon in $ADDON_LIST; do
  rm -fr $addon/*
done

popd > /dev/null

for addon in $ADDON_LIST; do
  addon_ver=$(xmlstarlet sel -t -m "/addon" -v "@version" $addon/addon.xml)
  echo -e "${COL_YELLOW}  create zip package:${COL_MAGENTA} $addon-$addon_ver.zip${COL_RESET}"
  zip -rq $REPO_DIR/$addon/$addon-$addon_ver.zip $addon
  cp -P $addon/addon.xml $REPO_DIR/$addon
  cp -P $addon/*.png $REPO_DIR/$addon 2>/dev/null || true
  cp -P $addon/*.jpg $REPO_DIR/$addon 2>/dev/null || true
  cp -P $addon/*.txt $REPO_DIR/$addon 2>/dev/null || true
  echo -e "${COL_YELLOW}     create md5sum's:${COL_MAGENTA} $addon-$addon_ver.zip.md5${COL_RESET}"
  ( cd $REPO_DIR/$addon
    md5sum -t $addon-$addon_ver.zip > $addon-$addon_ver.zip.md5;
  )
done

echo ""
echo -e "${COL_RED}Finish.${COL_RESET}"
echo ""
