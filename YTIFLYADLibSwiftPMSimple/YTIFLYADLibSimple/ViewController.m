//
//  ViewController.m
//  YTIFLYADLibSimple
//
//  Created by admin on 3.3.25.
//

#import "YTIFLYInterstitialViewController.h"
#import "YTIFLYSplashViewController.h"
#import "ViewController.h"

#import "YTIFLYADUtil.h"
#import <YTIFLYADLib/YTIFLYADLib.h>

@interface ViewController ()

@end

@implementation ViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    self.title = @"YTIFLYADLib 示例";
    self.view.backgroundColor = UIColor.whiteColor;
    [self initADTypeListView];
}

- (void)initADTypeListView {
    UIScrollView *scrollView = [[UIScrollView alloc] initWithFrame:self.view.bounds];
    scrollView.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
    [self.view addSubview:scrollView];

    CGFloat width = self.view.bounds.size.width;
    CGFloat margin = 24;
    CGFloat contentWidth = width - margin * 2;
    CGFloat y = 24;

    UILabel *versionLabel =
        [YTIFLYADUtil createSectionTitleWithText:[NSString stringWithFormat:@"SDK Version: %@", [YTIFLYAdTool ytifly_sdkVersion]]
                                         frame:CGRectMake(margin, y, contentWidth, 20)];
    versionLabel.textAlignment = NSTextAlignmentCenter;
    [scrollView addSubview:versionLabel];
    y += 36;

    UILabel *descLabel = [YTIFLYADUtil
        createSectionTitleWithText:@"本工程演示媒体侧常用接入流程：初始化、加载、展示、回调、销毁。示例代码只使用 SDK 公开 API。"
                             frame:CGRectMake(margin, y, contentWidth, 52)];
    descLabel.textAlignment = NSTextAlignmentCenter;
    [scrollView addSubview:descLabel];
    y += 72;

    NSArray<NSDictionary<NSString *, NSString *> *> *items = @[
        @{@"title" : @"开屏广告", @"selector" : @"splashADTypeClick:"},
        @{@"title" : @"插屏广告", @"selector" : @"interstitialADTypeClick:"},
    ];

    for (NSDictionary<NSString *, NSString *> *item in items) {
        SEL selector = NSSelectorFromString(item[@"selector"]);
        UIButton *button = [YTIFLYADUtil createADTypeButtonWithFrame:CGRectMake(margin, y, contentWidth, 48)
                                                             title:item[@"title"]
                                                            target:self
                                                            action:selector];
        [scrollView addSubview:button];
        y += 62;
    }

    scrollView.contentSize = CGSizeMake(width, y + 24);
}

- (void)splashADTypeClick:(UIButton *)sender {
    [self.navigationController pushViewController:YTIFLYSplashViewController.alloc.init animated:YES];
}

- (void)interstitialADTypeClick:(UIButton *)sender {
    [self.navigationController pushViewController:YTIFLYInterstitialViewController.alloc.init animated:YES];
}

@end
