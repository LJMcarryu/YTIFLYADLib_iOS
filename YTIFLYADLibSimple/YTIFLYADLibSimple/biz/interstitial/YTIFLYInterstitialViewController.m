#import "YTIFLYInterstitialViewController.h"

#import "YTIFLYADUtil.h"
#import <YTIFLYADLib/YTIFLYADLib.h>

@interface YTIFLYInterstitialViewController () <YTIFLYInterstitialAdDelegate>

@property (nonatomic, strong) YTIFLYInterstitialAd *interstitialAd;
@property (nonatomic, strong) UISegmentedControl *styleControl;
@property (nonatomic, strong) UIButton *showButton;
@property (nonatomic, strong) UILabel *statusLabel;
@property (nonatomic, strong) UITextView *logView;

@end

@implementation YTIFLYInterstitialViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    self.title = @"插屏广告";
    self.view.backgroundColor = UIColor.whiteColor;
    [self setupUI];
    [self log:@"插屏示例：Load -> Ready -> Show -> Close"];
}

- (void)dealloc {
    [self.interstitialAd ytifly_destroy];
}

- (void)setupUI {
    CGFloat margin = 16;
    CGFloat width = self.view.bounds.size.width;
    CGFloat contentWidth = width - margin * 2;
    CGFloat y = 110;

    UILabel *desc = [YTIFLYADUtil createSectionTitleWithText:@"插屏由 SDK 负责渲染和 present。媒体侧在 didReady 后传入展示配置并调用 show。"
                                                     frame:CGRectMake(margin, y, contentWidth, 38)];
    [self.view addSubview:desc];
    y += 48;

    self.styleControl = [[UISegmentedControl alloc] initWithItems:@[@"半屏", @"全屏"]];
    self.styleControl.frame = CGRectMake(margin, y, contentWidth, 32);
    self.styleControl.selectedSegmentIndex = 0;
    [self.view addSubview:self.styleControl];
    y += 48;

    CGFloat buttonWidth = (contentWidth - 8) / 2.0;
    UIButton *loadButton = [YTIFLYADUtil createADTypeButtonWithFrame:CGRectMake(margin, y, buttonWidth, 44)
                                                            title:@"Load"
                                                           target:self
                                                           action:@selector(ytifly_loadAd)];
    [self.view addSubview:loadButton];

    self.showButton = [YTIFLYADUtil createADTypeButtonWithFrame:CGRectMake(margin + buttonWidth + 8, y, buttonWidth, 44)
                                                        title:@"Show"
                                                       target:self
                                                       action:@selector(showAd)];
    [self setShowButtonEnabled:NO];
    [self.view addSubview:self.showButton];
    y += 54;

    UIButton *destroyButton = [YTIFLYADUtil createSmallButtonWithTitle:@"Destroy"
                                                               color:UIColor.systemRedColor
                                                              target:self
                                                              action:@selector(destroyAd)];
    destroyButton.frame = CGRectMake(margin, y, buttonWidth, 34);
    [self.view addSubview:destroyButton];

    UIButton *statusButton = [YTIFLYADUtil createSmallButtonWithTitle:@"检查状态"
                                                              color:UIColor.systemBlueColor
                                                             target:self
                                                             action:@selector(checkStatus)];
    statusButton.frame = CGRectMake(margin + buttonWidth + 8, y, buttonWidth, 34);
    [self.view addSubview:statusButton];
    y += 48;

    self.statusLabel = [[UILabel alloc] initWithFrame:CGRectMake(margin, y, contentWidth, 22)];
    self.statusLabel.font = [UIFont systemFontOfSize:13 weight:UIFontWeightMedium];
    self.statusLabel.textColor = UIColor.systemBlueColor;
    self.statusLabel.text = @"等待加载";
    [self.view addSubview:self.statusLabel];
    y += 34;

    UILabel *logTitle = [YTIFLYADUtil createSectionTitleWithText:@"回调日志"
                                                         frame:CGRectMake(margin, y, contentWidth, 18)];
    [self.view addSubview:logTitle];
    y += 22;

    CGFloat logHeight = MAX(260, self.view.bounds.size.height - y - 24);
    self.logView = [YTIFLYADUtil createLogTextViewWithFrame:CGRectMake(margin, y, contentWidth, logHeight)];
    [self.view addSubview:self.logView];
}

- (void)ytifly_loadAd {
    [self destroyAdSilently];
    [self setShowButtonEnabled:NO];
    [self updateStatus:@"正在加载插屏" color:UIColor.systemBlueColor];
    [self log:[NSString stringWithFormat:@"Load adUnitId=%@", __INTERSTITIAL_AD_UNIT_ID__]];

    YTIFLYInterstitialAd *ad = [[YTIFLYInterstitialAd alloc] initWithAdUnitId:__INTERSTITIAL_AD_UNIT_ID__];
    ad.delegate = self;
    ad.currentViewController = self;
    self.interstitialAd = ad;
    [ad ytifly_loadAdWithRequestConfig:[YTIFLYADUtil mediaSampleRequestConfig]];
}

- (void)showAd {
    if (!self.interstitialAd || ![self.interstitialAd ytifly_isAdValid]) {
        [self log:@"Show ignored: 插屏尚未 ready 或已失效"];
        [self updateStatus:@"请先等待 ready 回调" color:UIColor.systemRedColor];
        [self setShowButtonEnabled:NO];
        return;
    }

    YTIFLYInterstitialAdConfig *config = [[YTIFLYInterstitialAdConfig alloc] init];
    config.presentationStyle = self.styleControl.selectedSegmentIndex == 1
                                   ? YTIFLYInterstitialPresentationStyleFullScreen
                                   : YTIFLYInterstitialPresentationStyleHalfScreen;
    config.muteOnStart = YES;
    config.muteButtonHidden = NO;
    [self log:[NSString stringWithFormat:@"调用 show，style=%@", self.styleControl.selectedSegmentIndex == 1 ? @"全屏" : @"半屏"]];
    [self setShowButtonEnabled:NO];
    [self.interstitialAd ytifly_showAdFromRootViewController:self config:config];
}

- (void)destroyAd {
    [self destroyAdSilently];
    [self updateStatus:@"已销毁" color:[YTIFLYADUtil demoTealColor]];
    [self log:@"Destroy"];
}

- (void)checkStatus {
    [self log:[NSString stringWithFormat:@"状态 ytifly_isAdValid=%@ %@",
                                      (self.interstitialAd && [self.interstitialAd ytifly_isAdValid]) ? @"YES" : @"NO",
                                      [YTIFLYADUtil bidInfoSummaryForAd:self.interstitialAd]]];
}

- (void)destroyAdSilently {
    if (!self.interstitialAd) {
        return;
    }
    self.interstitialAd.delegate = nil;
    [self.interstitialAd ytifly_destroy];
    self.interstitialAd = nil;
    [self setShowButtonEnabled:NO];
}

- (void)setShowButtonEnabled:(BOOL)enabled {
    self.showButton.enabled = enabled;
    self.showButton.alpha = enabled ? 1.0 : 0.45;
}

- (void)updateStatus:(NSString *)text color:(UIColor *)color {
    self.statusLabel.text = text;
    self.statusLabel.textColor = color;
}

- (void)log:(NSString *)text {
    [YTIFLYADUtil appendLog:text toTextView:self.logView];
    YTIFLYSampleLogInfo(@"Interstitial", @"%@", text);
}

#pragma mark - YTIFLYInterstitialAdDelegate

- (void)ytifly_interstitialAdDidLoad:(YTIFLYInterstitialAd *)ad {
    [self log:[NSString stringWithFormat:@"interstitialAdDidLoad video=%@ landscape=%@ %@",
                                      ad.hasVideoTemplate ? @"YES" : @"NO",
                                      ad.isLandscapeTemplate ? @"YES" : @"NO",
                                      [YTIFLYADUtil bidInfoSummaryForAd:ad]]];
    [self updateStatus:@"已加载，等待素材 ready" color:[YTIFLYADUtil demoIndigoColor]];
}

- (void)ytifly_interstitialAdDidReady:(YTIFLYInterstitialAd *)ad {
    [self log:@"interstitialAdDidReady"];
    [self updateStatus:@"插屏已 ready，可展示" color:UIColor.systemGreenColor];
    [self setShowButtonEnabled:ad == self.interstitialAd && [ad ytifly_isAdValid]];
}

- (void)ytifly_interstitialAdDidShow:(YTIFLYInterstitialAd *)ad {
    [self log:@"interstitialAdDidShow"];
}

- (void)ytifly_interstitialAdDidRender:(YTIFLYInterstitialAd *)ad {
    [self log:@"interstitialAdDidRender"];
}

- (void)ytifly_interstitialAdDidExpose:(YTIFLYInterstitialAd *)ad {
    [self log:@"interstitialAdDidExpose"];
    [self updateStatus:@"插屏已曝光" color:UIColor.systemGreenColor];
}

- (void)ytifly_interstitialAdDidClick:(YTIFLYInterstitialAd *)ad {
    [self log:@"interstitialAdDidClick"];
}

- (void)ytifly_interstitialAdDidClose:(YTIFLYInterstitialAd *)ad {
    [self log:@"interstitialAdDidClose"];
    [self updateStatus:@"插屏已关闭" color:[YTIFLYADUtil demoTealColor]];
}

- (void)ytifly_interstitialAd:(YTIFLYInterstitialAd *)ad didFailWithError:(YTIFLYAdError *)error {
    [self log:[NSString stringWithFormat:@"interstitialAd didFailWithError %@", [YTIFLYADUtil summaryForError:error]]];
    [self updateStatus:@"插屏加载或展示失败" color:UIColor.systemRedColor];
    [self setShowButtonEnabled:NO];
}

- (void)ytifly_interstitialAd:(YTIFLYInterstitialAd *)ad didFailToRenderWithError:(YTIFLYAdError *)error {
    [self log:[NSString stringWithFormat:@"interstitialAd didFailToRender %@", [YTIFLYADUtil summaryForError:error]]];
}

- (void)ytifly_interstitialAd:(YTIFLYInterstitialAd *)ad didJumpWithSuccess:(BOOL)success {
    [self log:[NSString stringWithFormat:@"interstitialAd didJumpWithSuccess=%@", success ? @"YES" : @"NO"]];
}

@end
