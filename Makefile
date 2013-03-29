all: images

clean: clean_images

IMAGES_DIR = reddit_f2p/public/static/images
SMALL_IMAGES_DIR = $(IMAGES_DIR)/sm/
LARGE_IMAGES_DIR := $(IMAGES_DIR)/lg/
CURSOR_IMAGES_DIR := $(IMAGES_DIR)/cur/

SOURCE_IMAGES := $(notdir $(shell find art -name \*.png))
SMALL_IMAGES := $(addprefix $(SMALL_IMAGES_DIR), $(SOURCE_IMAGES))
LARGE_IMAGES := $(addprefix $(LARGE_IMAGES_DIR), $(SOURCE_IMAGES))
CURSOR_IMAGES := $(addprefix $(CURSOR_IMAGES_DIR), $(SOURCE_IMAGES))

images: $(SMALL_IMAGES_DIR) $(SMALL_IMAGES) $(LARGE_IMAGES_DIR) $(LARGE_IMAGES) $(CURSOR_IMAGES_DIR) $(CURSOR_IMAGES)
clean_images:
	rm -f $(SMALL_IMAGES) $(LARGE_IMAGES) $(CURSOR_IMAGES)

$(SMALL_IMAGES_DIR):
	mkdir -p $@

$(LARGE_IMAGES_DIR):
	mkdir -p $@

$(CURSOR_IMAGES_DIR):
	mkdir -p $@

$(SMALL_IMAGES_DIR)%.png : art/%.png
	convert -resize 60x60 $< -unsharp 0x0.5 $@

$(LARGE_IMAGES_DIR)%.png : art/%.png
	convert -resize 140x140 $< -unsharp 0x0.5 $@

$(CURSOR_IMAGES_DIR)%.png: art/%.png
	convert -resize 32x32 $< -unsharp 0x0.5 $@
