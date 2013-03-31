all: images

clean: clean_images

static:

IMAGES_DIR = reddit_f2p/public/static/images
SMALL_IMAGES_DIR = $(IMAGES_DIR)/sm/
LARGE_IMAGES_DIR := $(IMAGES_DIR)/lg/
HAT_IMAGES_DIR := $(IMAGES_DIR)/hat/
CURSOR_IMAGES_DIR := $(IMAGES_DIR)/cur/
SILHOUETTE_IMAGES_DIR := $(IMAGES_DIR)/sil/
ALL_DIRS := $(SMALL_IMAGES_DIR) $(LARGE_IMAGES_DIR) $(HAT_IMAGES_DIR) $(CURSOR_IMAGES_DIR) $(SILHOUETTE_IMAGES_DIR)

SOURCE_IMAGES := $(notdir $(shell find art -name \*.png))
HAT_SOURCE_IMAGES := $(filter %_hat.png, $(SOURCE_IMAGES))
SMALL_IMAGES := $(addprefix $(SMALL_IMAGES_DIR), $(SOURCE_IMAGES))
LARGE_IMAGES := $(addprefix $(LARGE_IMAGES_DIR), $(SOURCE_IMAGES))
HAT_IMAGES := $(addprefix $(HAT_IMAGES_DIR), $(HAT_SOURCE_IMAGES))
CURSOR_IMAGES := $(addprefix $(CURSOR_IMAGES_DIR), $(SOURCE_IMAGES))
SILHOUETTE_IMAGES := $(addprefix $(SILHOUETTE_IMAGES_DIR), $(SOURCE_IMAGES))
ALL_IMAGES := $(SMALL_IMAGES) $(LARGE_IMAGES) $(HAT_IMAGES) $(CURSOR_IMAGES) $(SILHOUETTE_IMAGES)

CONVERT := convert
CONVERT_SQUARE := $(CONVERT) -background none -gravity center -extent 500x500

images: $(ALL_DIRS) $(ALL_IMAGES)
clean_images:
	rm -f $(ALL_IMAGES)
	- rmdir $(ALL_DIRS)

$(ALL_DIRS):
	mkdir -p $@

$(SMALL_IMAGES_DIR)%.png : art/%.png
	$(CONVERT_SQUARE) -resize 60x60 $< -unsharp 0x0.5 $@

$(LARGE_IMAGES_DIR)%.png : art/%.png
	$(CONVERT_SQUARE) -resize 140x140 $< -unsharp 0x0.5 $@

$(HAT_IMAGES_DIR)%.png : art/%.png
	$(CONVERT) -resize 24x24 $< -channel RGBA -unsharp 0x0.5 $@

$(CURSOR_IMAGES_DIR)%.png: art/%.png
	$(CONVERT_SQUARE) -resize 32x32 $< -unsharp 0x2 $@

$(SILHOUETTE_IMAGES_DIR)%.png: art/%.png
	$(CONVERT_SQUARE) -resize 24x24 -channel RGB -threshold 100% -channel A -normalize $< -unsharp 0x0.5 $@
