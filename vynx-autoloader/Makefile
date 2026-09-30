# Vynx.dev Autoloader native PS5 installer

PYTHON ?= python3
CC     := /opt/ps5-payload-sdk/bin/prospero-clang
STRIP  := /opt/ps5-payload-sdk/bin/prospero-strip

SDK      := /opt/ps5-payload-sdk
TARGET   := $(SDK)/target
INCLUDES := -Iinclude -I$(TARGET)/include
LIBS     := $(TARGET)/lib/libmicrohttpd.a \
            -L$(TARGET)/lib -lpthread \
            -lSceNetCtl -lSceUserService -lSceSystemService \
            -lSceAppInstUtil

SRCS := src/main.c src/http_server.c src/app_installer.c \
        src/notification.c src/ps5_launcher.c src/log.c src/inflate.c \
        src/webkit_cleaner.c src/simulate_corrupt.c
ELF := vynx-autoloader-installer.elf

FILE_REGISTRY_H := include/file_registry.h
FILE_REGISTRY_C := include/file_registry.c
FILE_REGISTRY_STAMP := include/.file_registry.stamp
VERSION_HEADER := include/vynxi_version.h

FRONTEND_INSTALLER_PAGE := frontend/installer-page
FRONTEND_POINTER := frontend/pointer
FRONTEND_VYNX := frontend/vynx
FRONTEND_STAGE := frontend/dist
FRONTEND_FILES := $(shell find $(FRONTEND_INSTALLER_PAGE) $(FRONTEND_POINTER) $(FRONTEND_VYNX) -type f 2>/dev/null)

ICON_SOURCE := assets/icon-source.png
ICON0 := assets/icon0.png

HOST := vynx-autoloader-host.py
HOST_PAYLOAD ?= $(ELF)

CFLAGS  := -Os -Wall -ffunction-sections -fdata-sections $(INCLUDES)
LDFLAGS := -Wl,--gc-sections

SIMULATE ?= 0
ifeq ($(SIMULATE),1)
CFLAGS += -DVYNXI_SIMULATE_CACHE_CORRUPTION=1
else ifeq ($(SIMULATE),2)
CFLAGS += -DVYNXI_SIMULATE_CACHE_CORRUPTION=2
endif

.PHONY: all version print-version icons host clean

all: $(ELF)

version:
	$(PYTHON) tools/gen_version.py

print-version:
	@$(PYTHON) tools/gen_version.py --print

icons: $(ICON0)

$(ICON0): $(ICON_SOURCE) tools/gen_icon.py
	$(PYTHON) tools/gen_icon.py

$(FILE_REGISTRY_H) $(FILE_REGISTRY_C): $(FILE_REGISTRY_STAMP)

$(FILE_REGISTRY_STAMP): $(FRONTEND_FILES) version icons
	@V=$$($(PYTHON) tools/gen_version.py --print); \
	rm -rf $(FRONTEND_STAGE) && \
	mkdir -p $(FRONTEND_STAGE)/app/v$$V && \
	cp -R $(FRONTEND_INSTALLER_PAGE)/. $(FRONTEND_STAGE)/ && \
	cp -R $(FRONTEND_POINTER)/. $(FRONTEND_STAGE)/app/ && \
	cp -R $(FRONTEND_VYNX)/. $(FRONTEND_STAGE)/app/v$$V/ && \
	echo "$$V" > $(FRONTEND_STAGE)/VERSION
	$(PYTHON) tools/gen_file_registry.py $(FRONTEND_STAGE) $(FILE_REGISTRY_H) $(FILE_REGISTRY_C)
	@touch $(FILE_REGISTRY_STAMP)

$(ELF): $(FILE_REGISTRY_H) $(FILE_REGISTRY_C) $(SRCS) $(ICON0)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $(ELF) $(SRCS) $(FILE_REGISTRY_C) $(LIBS)
	$(STRIP) $(ELF)

$(HOST): $(FRONTEND_FILES) version $(HOST_PAYLOAD)
	$(PYTHON) tools/build_host.py --frontend $(FRONTEND_VYNX) \
		--overrides pc-host/overrides --input pc-host/host.py \
		--output $(HOST) --payload $(HOST_PAYLOAD)

host: $(HOST)

clean:
	rm -rf $(FRONTEND_STAGE)
	rm -f $(ELF) $(FILE_REGISTRY_H) $(FILE_REGISTRY_C) \
		$(FILE_REGISTRY_STAMP) $(VERSION_HEADER) assets/param.json $(HOST)
