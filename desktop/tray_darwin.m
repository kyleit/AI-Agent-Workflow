#import <Cocoa/Cocoa.h>

extern void trayCallbackShow();
extern void trayCallbackHide();
extern void trayCallbackQuit();

@interface TrayMenuHandler : NSObject
- (void)showApp:(id)sender;
- (void)hideApp:(id)sender;
- (void)quitApp:(id)sender;
@end

@implementation TrayMenuHandler
- (void)showApp:(id)sender {
    trayCallbackShow();
}
- (void)hideApp:(id)sender {
    trayCallbackHide();
}
- (void)quitApp:(id)sender {
    trayCallbackQuit();
}
@end

static NSStatusItem *statusItem;
static TrayMenuHandler *menuHandler;

void initSystray(const char* iconPath) {
    NSString *path = nil;
    if (iconPath != NULL) {
        path = [NSString stringWithUTF8String:iconPath];
#if !__has_feature(objc_arc)
        [path retain];
#endif
    }

    dispatch_async(dispatch_get_main_queue(), ^{
        statusItem = [[NSStatusBar systemStatusBar] statusItemWithLength:NSVariableStatusItemLength];
#if !__has_feature(objc_arc)
        [statusItem retain];
#endif

        NSString *fileName = path ? [path lastPathComponent] : @"(null)";
        NSLog(@"initSystray: starting initialization with icon: %@", fileName);

        NSImage *image = nil;
        if (path != nil) {
            image = [[NSImage alloc] initWithContentsOfFile:path];
        }

        statusItem.button.title = @"AIWF";
        statusItem.button.toolTip = @"AIWF Framework";

        if (image != nil) {
            [image setSize:NSMakeSize(18, 18)];
            [image setTemplate:YES];
            statusItem.button.image = image;
            statusItem.button.imagePosition = NSImageLeft;
            NSLog(@"initSystray: icon %@ loaded successfully", fileName);
#if !__has_feature(objc_arc)
            [image release];
#endif
        } else {
            statusItem.button.imagePosition = NSNoImage;
            NSLog(@"initSystray warning: failed to load icon from file: %@", fileName);
        }

        menuHandler = [[TrayMenuHandler alloc] init];

        NSMenu *menu = [[NSMenu alloc] init];

        NSMenuItem *showItem = [[NSMenuItem alloc] initWithTitle:@"Show AIWF Framework" action:@selector(showApp:) keyEquivalent:@""];
        [showItem setTarget:menuHandler];
        [menu addItem:showItem];

        NSMenuItem *hideItem = [[NSMenuItem alloc] initWithTitle:@"Hide AIWF Framework" action:@selector(hideApp:) keyEquivalent:@""];
        [hideItem setTarget:menuHandler];
        [menu addItem:hideItem];

        [menu addItem:[NSMenuItem separatorItem]];

        NSMenuItem *quitItem = [[NSMenuItem alloc] initWithTitle:@"Quit AIWF Framework" action:@selector(quitApp:) keyEquivalent:@""];
        [quitItem setTarget:menuHandler];
        [menu addItem:quitItem];

        statusItem.menu = menu;

        // Log final readiness line including title, length, and button frame width
        NSLog(@"initSystray readiness: title=%@, length=%.2f, width=%.2f", statusItem.button.title, statusItem.length, statusItem.button.frame.size.width);

#if !__has_feature(objc_arc)
        [showItem release];
        [hideItem release];
        [quitItem release];
        [menu release];
        if (path != nil) {
            [path release];
        }
#endif
    });
}
