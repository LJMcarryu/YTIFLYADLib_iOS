//
//  AppDelegate.m
//  YTIFLYADLibSimple
//
//  Created by admin on 3.3.25.
//

#import "AppDelegate.h"
#import "ViewController.h"

#import <AppTrackingTransparency/AppTrackingTransparency.h>
#import <YTIFLYADLib/YTIFLYADLib.h>

@interface AppDelegate ()

@property (nonatomic, assign) BOOL didRequestTrackingAuthorization;

@end

@implementation AppDelegate


- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
    self.window = [[UIWindow alloc] initWithFrame:[UIScreen mainScreen].bounds];
    ViewController *rootViewController = [[ViewController alloc] init];
    UINavigationController *navigationController = [[UINavigationController alloc] initWithRootViewController:rootViewController];
    self.window.rootViewController = navigationController;
    [self.window makeKeyAndVisible];

    /// 设置是否开启个性化推荐
    [YTIFLYAdConfig ytifly_setPersonalizedEnabled:YES];
    /// 示例工程默认开启日志，媒体正式上线前可关闭。
    [YTIFLYAdConfig ytifly_setLogEnabled:YES];

    return YES;
}

- (void)applicationDidBecomeActive:(UIApplication *)application {
    [self requestTrackingAuthorizationIfNeeded];
}

- (void)requestTrackingAuthorizationIfNeeded {
    if (@available(iOS 14, *)) {
        if (self.didRequestTrackingAuthorization) {
            return;
        }

        ATTrackingManagerAuthorizationStatus currentStatus = ATTrackingManager.trackingAuthorizationStatus;
        if (currentStatus != ATTrackingManagerAuthorizationStatusNotDetermined) {
            self.didRequestTrackingAuthorization = YES;
            YTIFLYSampleLogInfo(@"ATT", @"trackingAuthorizationStatus=%ld", (long)currentStatus);
            return;
        }

        self.didRequestTrackingAuthorization = YES;
        [ATTrackingManager requestTrackingAuthorizationWithCompletionHandler:^(ATTrackingManagerAuthorizationStatus status) {
            YTIFLYSampleLogInfo(@"ATT", @"trackingAuthorizationStatus=%ld", (long)status);
        }];
    }
}

@end
