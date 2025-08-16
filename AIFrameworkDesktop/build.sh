#!/bin/bash
# Build Script for AI Framework Desktop - M3 Max Optimized

echo "🍎 Building AI Framework Desktop for M3 Max"
echo "============================================="

# Check if we're on Apple Silicon
if [[ $(uname -m) != "arm64" ]]; then
    echo "❌ This build script is designed for Apple Silicon Macs"
    echo "   Detected architecture: $(uname -m)"
    exit 1
fi

# Check macOS version
MACOS_VERSION=$(sw_vers -productVersion)
MACOS_MAJOR=$(echo $MACOS_VERSION | cut -d. -f1)

if [[ $MACOS_MAJOR -lt 13 ]]; then
    echo "❌ macOS 13.0+ (Ventura) required for this app"
    echo "   Current version: $MACOS_VERSION"
    exit 1
fi

echo "✅ macOS version: $MACOS_VERSION"
echo "✅ Architecture: $(uname -m)"

# Check Xcode installation
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Xcode not found. Please install Xcode from the App Store"
    exit 1
fi

XCODE_VERSION=$(xcodebuild -version | head -n 1)
echo "✅ Xcode: $XCODE_VERSION"

# Check Swift version
if ! command -v swift &> /dev/null; then
    echo "❌ Swift not found. Please install Xcode command line tools"
    exit 1
fi

SWIFT_VERSION=$(swift --version | head -n 1)
echo "✅ Swift: $SWIFT_VERSION"

# Create Xcode project if it doesn't exist
if [ ! -f "AIFrameworkApp.xcodeproj" ]; then
    echo "📱 Creating Xcode project..."

    # Create project structure
    mkdir -p AIFrameworkApp
    mkdir -p AIFrameworkApp/Views
    mkdir -p AIFrameworkApp/Models
    mkdir -p AIFrameworkApp/ViewModels
    mkdir -p AIFrameworkApp/Services

    # Move main app file
    mv AIFrameworkApp.swift AIFrameworkApp/

    # Create project file
    cat > AIFrameworkApp.xcodeproj/project.pbxproj << 'EOF'
// !$*UTF8*$!
{
	archiveVersion = 1;
	classes = {
	};
	objectVersion = 56;
	objects = {

/* Begin PBXBuildFile section */
		A1B2C3D4E5F6789012345678 /* AIFrameworkApp.swift in Sources */ = {isa = PBXBuildFile; fileRef = A1B2C3D4E5F6789012345679 /* AIFrameworkApp.swift */; };
		A1B2C3D4E5F6789012345680 /* Info.plist in Resources */ = {isa = PBXBuildFile; fileRef = A1B2C3D4E5F6789012345681 /* Info.plist */; };
		A1B2C3D4E5F6789012345682 /* Entitlements.plist in Resources */ = {isa = PBXBuildFile; fileRef = A1B2C3D4E5F6789012345683 /* Entitlements.plist */; };
/* End PBXBuildFile section */

/* Begin PBXFileReference section */
		A1B2C3D4E5F6789012345679 /* AIFrameworkApp.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = AIFrameworkApp.swift; sourceTree = "<group>"; };
		A1B2C3D4E5F6789012345681 /* Info.plist */ = {isa = PBXFileReference; lastKnownFileType = text.plist.xml; path = Info.plist; sourceTree = "<group>"; };
		A1B2C3D4E5F6789012345683 /* Entitlements.plist */ = {isa = PBXFileReference; lastKnownFileType = text.plist.entitlements; path = Entitlements.plist; sourceTree = "<group>"; };
		A1B2C3D4E5F6789012345684 /* AIFrameworkApp.app */ = {isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = AIFrameworkApp.app; sourceTree = BUILT_PRODUCTS_DIR; };
/* End PBXFileReference section */

/* Begin PBXFrameworksBuildPhase section */
		A1B2C3D4E5F6789012345685 /* Frameworks */ = {
			isa = PBXFrameworksBuildPhase;
			buildActionMask = 2147483647;
			files = (
			);
			runOnlyForDeploymentPostprocessing = 0;
		};
/* End PBXFrameworksBuildPhase section */

/* Begin PBXGroup section */
		A1B2C3D4E5F6789012345686 = {
			isa = PBXGroup;
			children = (
				A1B2C3D4E5F6789012345687 /* AIFrameworkApp */,
				A1B2C3D4E5F6789012345688 /* Products */,
			);
			sourceTree = "<group>";
		};
		A1B2C3D4E5F6789012345687 /* AIFrameworkApp */ = {
			isa = PBXGroup;
			children = (
				A1B2C3D4E5F6789012345679 /* AIFrameworkApp.swift */,
				A1B2C3D4E5F6789012345681 /* Info.plist */,
				A1B2C3D4E5F6789012345683 /* Entitlements.plist */,
			);
			path = AIFrameworkApp;
			sourceTree = "<group>";
		};
		A1B2C3D4E5F6789012345688 /* Products */ = {
			isa = PBXGroup;
			children = (
				A1B2C3D4E5F6789012345684 /* AIFrameworkApp.app */,
			);
			name = Products;
			sourceTree = "<group>";
		};
/* End PBXGroup section */

/* Begin PBXNativeTarget section */
		A1B2C3D4E5F6789012345689 /* AIFrameworkApp */ = {
			isa = PBXNativeTarget;
			buildConfigurationList = A1B2C3D4E5F6789012345690 /* Build configuration list for PBXNativeTarget "AIFrameworkApp" */;
			buildPhases = (
				A1B2C3D4E5F6789012345691 /* Sources */,
				A1B2C3D4E5F6789012345685 /* Frameworks */,
				A1B2C3D4E5F6789012345692 /* Resources */,
			);
			buildRules = (
			);
			dependencies = (
			);
			name = AIFrameworkApp;
			productName = AIFrameworkApp;
			productReference = A1B2C3D4E5F6789012345684 /* AIFrameworkApp.app */;
			productType = "com.apple.product-type.application";
		};
/* End PBXNativeTarget section */

/* Begin PBXProject section */
		A1B2C3D4E5F6789012345693 /* Project object */ = {
			isa = PBXProject;
			attributes = {
				BuildIndependentTargetsInParallel = 1;
				LastSwiftUpdateCheck = 1500;
				LastUpgradeCheck = 1500;
				TargetAttributes = {
					A1B2C3D4E5F6789012345689 = {
						CreatedOnToolsVersion = 15.0;
					};
				};
			};
			buildConfigurationList = A1B2C3D4E5F6789012345694 /* Build configuration list for PBXProject "AIFrameworkApp" */;
			compatibilityVersion = "Xcode 14.0";
			developmentRegion = en;
			hasScannedForEncodings = 0;
			knownRegions = (
				en,
				Base,
			);
			mainGroup = A1B2C3D4E5F6789012345686;
			productRefGroup = A1B2C3D4E5F6789012345688 /* Products */;
			projectDirPath = "";
			projectRoot = "";
			targets = (
				A1B2C3D4E5F6789012345689 /* AIFrameworkApp */,
			);
		};
/* End PBXProject section */

/* Begin PBXResourcesBuildPhase section */
		A1B2C3D4E5F6789012345692 /* Resources */ = {
			isa = PBXResourcesBuildPhase;
			buildActionMask = 2147483647;
			files = (
				A1B2C3D4E5F6789012345680 /* Info.plist in Resources */,
				A1B2C3D4E5F6789012345682 /* Entitlements.plist in Resources */;
			);
			runOnlyForDeploymentPostprocessing = 0;
		};
/* End PBXResourcesBuildPhase section */

/* Begin PBXSourcesBuildPhase section */
		A1B2C3D4E5F6789012345691 /* Sources */ = {
			isa = PBXSourcesBuildPhase;
			buildActionMask = 2147483647;
			files = (
				A1B2C3D4E5F6789012345678 /* AIFrameworkApp.swift in Sources */,
			);
			runOnlyForDeploymentPostprocessing = 0;
		};
/* End PBXSourcesBuildPhase section */

/* Begin XCBuildConfiguration section */
		A1B2C3D4E5F6789012345695 /* Debug */ = {
			isa = XCBuildConfiguration;
			buildSettings = {
				ALWAYS_SEARCH_USER_PATHS = NO;
				ASSETCATALOG_COMPILER_GENERATE_SWIFT_ASSET_SYMBOL_EXTENSIONS = YES;
				CLANG_ANALYZER_NONNULL = YES;
				CLANG_ANALYZER_NUMBER_OBJECT_CONVERSION = YES_AGGRESSIVE;
				CLANG_CXX_LANGUAGE_STANDARD = "gnu++20";
				CLANG_ENABLE_MODULES = YES;
				CLANG_ENABLE_OBJC_ARC = YES;
				CLANG_ENABLE_OBJC_WEAK = YES;
				CLANG_WARN_BLOCK_CAPTURE_AUTORELEASING = YES;
				CLANG_WARN_BOOL_CONVERSION = YES;
				CLANG_WARN_COMMA = YES;
				CLANG_WARN_CONSTANT_CONVERSION = YES;
				CLANG_WARN_DEPRECATED_OBJC_IMPLEMENTATIONS = YES;
				CLANG_WARN_DIRECT_OBJC_ISA_USAGE = YES_ERROR;
				CLANG_WARN_DOCUMENTATION_COMMENTS = YES;
				CLANG_WARN_EMPTY_BODY = YES;
				CLANG_WARN_ENUM_CONVERSION = YES;
				CLANG_WARN_INFINITE_RECURSION = YES;
				CLANG_WARN_INT_CONVERSION = YES;
				CLANG_WARN_NON_LITERAL_NULL_CONVERSION = YES;
				CLANG_WARN_OBJC_IMPLICIT_RETAIN_SELF = YES;
				CLANG_WARN_OBJC_LITERAL_CONVERSION = YES;
				CLANG_WARN_OBJC_ROOT_CLASS = YES_ERROR;
				CLANG_WARN_QUOTED_INCLUDE_IN_FRAMEWORK_HEADER = YES;
				CLANG_WARN_RANGE_LOOP_ANALYSIS = YES;
				CLANG_WARN_STRICT_PROTOTYPES = YES;
				CLANG_WARN_SUSPICIOUS_MOVE = YES;
				CLANG_WARN_UNGUARDED_AVAILABILITY = YES_AGGRESSIVE;
				CLANG_WARN_UNREACHABLE_CODE = YES;
				CLANG_WARN__DUPLICATE_METHOD_MATCH = YES;
				COPY_PHASE_STRIP = NO;
				DEBUG_INFORMATION_FORMAT = dwarf;
				ENABLE_STRICT_OBJC_MSGSEND = YES;
				ENABLE_TESTABILITY = YES;
				ENABLE_USER_SCRIPT_SANDBOXING = YES;
				GCC_C_LANGUAGE_STANDARD = gnu17;
				GCC_DYNAMIC_NO_PIC = NO;
				GCC_NO_COMMON_BLOCKS = YES;
				GCC_OPTIMIZATION_LEVEL = 0;
				GCC_PREPROCESSOR_DEFINITIONS = (
					"DEBUG=1",
					"$(inherited)",
				);
				GCC_WARN_64_TO_32_BIT_CONVERSION = YES;
				GCC_WARN_ABOUT_RETURN_TYPE = YES_ERROR;
				GCC_WARN_UNDECLARED_SELECTOR = YES;
				GCC_WARN_UNINITIALIZED_AUTOS = YES_AGGRESSIVE;
				GCC_WARN_UNUSED_FUNCTION = YES;
				GCC_WARN_UNUSED_VARIABLE = YES;
				LOCALIZATION_PREFERS_STRING_CATALOGS = YES;
				MACOSX_DEPLOYMENT_TARGET = 13.0;
				MTL_ENABLE_DEBUG_INFO = INCLUDE_SOURCE;
				MTL_FAST_MATH = YES;
				ONLY_ACTIVE_ARCH = YES;
				SDKROOT = macosx;
				SWIFT_ACTIVE_COMPILATION_CONDITIONS = "DEBUG $(inherited)";
				SWIFT_OPTIMIZATION_LEVEL = "-Onone";
			};
			name = Debug;
		};
		A1B2C3D4E5F6789012345696 /* Release */ = {
			isa = XCBuildConfiguration;
			buildSettings = {
				ALWAYS_SEARCH_USER_PATHS = NO;
				ASSETCATALOG_COMPILER_GENERATE_SWIFT_ASSET_SYMBOL_EXTENSIONS = YES;
				CLANG_ANALYZER_NONNULL = YES;
				CLANG_ANALYZER_NUMBER_OBJECT_CONVERSION = YES_AGGRESSIVE;
				GCC_C_LANGUAGE_STANDARD = gnu17;
				GCC_DYNAMIC_NO_PIC = NO;
				GCC_NO_COMMON_BLOCKS = YES;
				GCC_WARN_64_TO_32_BIT_CONVERSION = YES;
				GCC_WARN_ABOUT_RETURN_TYPE = YES_ERROR;
				GCC_WARN_UNDECLARED_SELECTOR = YES;
				GCC_WARN_UNINITIALIZED_AUTOS = YES_AGGRESSIVE;
				GCC_WARN_UNUSED_FUNCTION = YES;
				GCC_WARN_UNUSED_VARIABLE = YES;
				LOCALIZATION_PREFERS_STRING_CATALOGS = YES;
				MACOSX_DEPLOYMENT_TARGET = 13.0;
				MTL_ENABLE_DEBUG_INFO = NO;
				MTL_FAST_MATH = YES;
				SDKROOT = macosx;
				SWIFT_COMPILATION_MODE = wholemodule;
				SWIFT_OPTIMIZATION_LEVEL = "-O";
			};
			name = Release;
		};
		A1B2C3D4E5F6789012345697 /* Debug */ = {
			isa = XCBuildConfiguration;
			buildSettings = {
				ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon;
				ASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME = AccentColor;
				CODE_SIGN_ENTITLEMENTS = AIFrameworkApp/Entitlements.plist;
				CODE_SIGN_STYLE = Automatic;
				COMBINE_HIDPI_IMAGES = YES;
				CURRENT_PROJECT_VERSION = 1;
				DEVELOPMENT_TEAM = "";
				ENABLE_HARDENED_RUNTIME = YES;
				ENABLE_PREVIEWS = YES;
				GENERATE_INFOPLIST_FILE = YES;
				INFOPLIST_FILE = AIFrameworkApp/Info.plist;
				INFOPLIST_KEY_NSHumanReadableCopyright = "";
				LD_RUNPATH_SEARCH_PATHS = (
					"$(inherited)",
					"@executable_path/../Frameworks",
				);
				MARKETING_VERSION = 1.0;
				PRODUCT_BUNDLE_IDENTIFIER = com.aiframework.desktop;
				PRODUCT_NAME = "$(TARGET_NAME)";
				SWIFT_EMIT_LOC_STRINGS = YES;
				SWIFT_VERSION = 5.0;
			};
			name = Debug;
		};
		A1B2C3D4E5F6789012345698 /* Release */ = {
			isa = XCBuildConfiguration;
			buildSettings = {
				ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon;
				ASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME = AccentColor;
				CODE_SIGN_ENTITLEMENTS = AIFrameworkApp/Entitlements.plist;
				CODE_SIGN_STYLE = Automatic;
				COMBINE_HIDPI_IMAGES = YES;
				CURRENT_PROJECT_VERSION = 1;
				DEVELOPMENT_TEAM = "";
				ENABLE_HARDENED_RUNTIME = YES;
				ENABLE_PREVIEWS = YES;
				GENERATE_INFOPLIST_FILE = YES;
				INFOPLIST_FILE = AIFrameworkApp/Info.plist;
				INFOPLIST_KEY_NSHumanReadableCopyright = "";
				LD_RUNPATH_SEARCH_PATHS = (
					"$(inherited)",
					"@executable_path/../Frameworks",
				);
				MARKETING_VERSION = 1.0;
				PRODUCT_BUNDLE_IDENTIFIER = com.aiframework.desktop;
				PRODUCT_NAME = "$(TARGET_NAME)";
				SWIFT_EMIT_LOC_STRINGS = YES;
				SWIFT_VERSION = 5.0;
			};
			name = Release;
		};
/* End XCBuildConfiguration section */

/* Begin XCConfigurationList section */
		A1B2C3D4E5F6789012345694 /* Build configuration list for PBXProject "AIFrameworkApp" */ = {
			isa = XCConfigurationList;
			buildConfigurations = (
				A1B2C3D4E5F6789012345695 /* Debug */,
				A1B2C3D4E5F6789012345696 /* Release */,
			);
			defaultConfigurationIsVisible = 0;
			defaultConfigurationName = Release;
		};
		A1B2C3D4E5F6789012345690 /* Build configuration list for PBXNativeTarget "AIFrameworkApp" */ = {
			isa = XCConfigurationList;
			buildConfigurations = (
				A1B2C3D4E5F6789012345697 /* Debug */,
				A1B2C3D4E5F6789012345698 /* Release */,
			);
			defaultConfigurationIsVisible = 0;
			defaultConfigurationName = Release;
		};
/* End XCConfigurationList section */
	};
	rootObject = A1B2C3D4E5F6789012345693 /* Project object */;
}
EOF

    echo "✅ Xcode project created"
else
    echo "✅ Xcode project already exists"
fi

# Build the application
echo "🔨 Building AI Framework Desktop..."
echo "   Target: macOS ARM64"
echo "   Deployment: macOS 13.0+"

# Clean build
xcodebuild clean -project AIFrameworkApp.xcodeproj -scheme AIFrameworkApp -configuration Debug

# Build
xcodebuild build -project AIFrameworkApp.xcodeproj -scheme AIFrameworkApp -configuration Debug -destination 'platform=macOS,arch=arm64'

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Build successful!"
    echo "===================="
    echo "📱 App location: build/Debug/AIFrameworkApp.app"
    echo ""
    echo "🚀 To run the app:"
    echo "   open build/Debug/AIFrameworkApp.app"
    echo ""
    echo "🔧 To open in Xcode for development:"
    echo "   open AIFrameworkApp.xcodeproj"
    echo ""
    echo "📊 Current M3 Max services status:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo ""
    echo "❌ Build failed!"
    echo "================"
    echo "Please check the error messages above"
    echo ""
    echo "💡 Common solutions:"
    echo "   1. Ensure Xcode is properly installed"
    echo "   2. Check that all files are in the correct locations"
    echo "   3. Verify macOS version compatibility"
    echo "   4. Try opening the project in Xcode manually"
    exit 1
fi
