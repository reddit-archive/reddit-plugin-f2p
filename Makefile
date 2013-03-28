all: images

clean: clean_images

IMAGES_DIR = reddit_f2p/public/static/images
SMALL_IMAGES_DIR = $(IMAGES_DIR)/sm/

SOURCE_IMAGES := $(notdir $(shell find art -name \*.png))
SMALL_IMAGES := $(addprefix $(SMALL_IMAGES_DIR), $(SOURCE_IMAGES))

images: $(SMALL_IMAGES_DIR) $(SMALL_IMAGES)
clean_images:
	rm -f $(SMALL_IMAGES)

$(SMALL_IMAGES_DIR):
	mkdir -p $@

reddit_f2p/public/static/images/sm/%.png : art/%.png
	convert -resize 60x60 $< -unsharp 0x0.5 $@
