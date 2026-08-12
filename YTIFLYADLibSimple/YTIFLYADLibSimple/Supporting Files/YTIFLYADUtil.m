//
//  YTIFLYADUtil.m
//  YTIFLYADLibSimple
//
//  Created by admin on 6.3.25.
//

#import "YTIFLYADUtil.h"

#import <AdSupport/AdSupport.h>
#import <AppTrackingTransparency/AppTrackingTransparency.h>
#import <YTIFLYADLib/YTIFLYADLib.h>

@implementation YTIFLYADUtil

+ (UIButton *)createADTypeButtonWithFrame:(CGRect)frame
                                    title:(NSString *)title
                                   target:(nullable id)target
                                   action:(SEL)action {
    UIButton *button = [UIButton buttonWithType:UIButtonTypeSystem];
    button.frame = frame;
    [button setTitle:title forState:UIControlStateNormal];
    [button addTarget:target action:action forControlEvents:UIControlEventTouchUpInside];
    [button setTitleColor:[UIColor whiteColor] forState:UIControlStateNormal];
    button.backgroundColor = [UIColor blackColor];
    button.layer.cornerRadius = 8;
    button.clipsToBounds = YES;
    button.titleLabel.font = [UIFont systemFontOfSize:15 weight:UIFontWeightMedium];
    button.titleLabel.adjustsFontSizeToFitWidth = YES;
    button.titleLabel.minimumScaleFactor = 0.75;
    return button;
}

+ (UIButton *)createSmallButtonWithTitle:(NSString *)title
                                   color:(UIColor *)color
                                  target:(nullable id)target
                                  action:(SEL)action {
    UIButton *button = [UIButton buttonWithType:UIButtonTypeSystem];
    [button setTitle:title forState:UIControlStateNormal];
    [button setTitleColor:UIColor.whiteColor forState:UIControlStateNormal];
    [button addTarget:target action:action forControlEvents:UIControlEventTouchUpInside];
    button.backgroundColor = color;
    button.layer.cornerRadius = 6;
    button.clipsToBounds = YES;
    button.titleLabel.font = [UIFont systemFontOfSize:13 weight:UIFontWeightMedium];
    button.titleLabel.adjustsFontSizeToFitWidth = YES;
    button.titleLabel.minimumScaleFactor = 0.75;
    return button;
}

+ (UILabel *)createSectionTitleWithText:(NSString *)text frame:(CGRect)frame {
    UILabel *label = [[UILabel alloc] initWithFrame:frame];
    label.text = text;
    label.textColor = [self demoSecondaryLabelColor];
    label.font = [UIFont systemFontOfSize:13 weight:UIFontWeightRegular];
    label.numberOfLines = 0;
    return label;
}

+ (UITextView *)createLogTextViewWithFrame:(CGRect)frame {
    UITextView *textView = [[UITextView alloc] initWithFrame:frame];
    textView.editable = NO;
    textView.selectable = YES;
    textView.font = [UIFont fontWithName:@"Menlo" size:11] ?: [UIFont systemFontOfSize:11];
    textView.textColor = UIColor.darkTextColor;
    textView.backgroundColor = [UIColor colorWithWhite:0.96 alpha:1.0];
    textView.layer.cornerRadius = 8;
    textView.layer.borderColor = [UIColor colorWithWhite:0.86 alpha:1.0].CGColor;
    textView.layer.borderWidth = 1;
    textView.textContainerInset = UIEdgeInsetsMake(8, 6, 8, 6);
    return textView;
}

+ (UIColor *)demoSecondaryLabelColor {
    if (@available(iOS 13.0, *)) {
        return UIColor.secondaryLabelColor;
    }
    return UIColor.grayColor;
}

+ (UIColor *)demoIndigoColor {
    if (@available(iOS 13.0, *)) {
        return UIColor.systemIndigoColor;
    }
    return [UIColor colorWithRed:0.35 green:0.34 blue:0.84 alpha:1.0];
}

+ (UIColor *)demoTealColor {
    if (@available(iOS 13.0, *)) {
        return UIColor.systemTealColor;
    }
    return [UIColor colorWithRed:0.35 green:0.78 blue:0.98 alpha:1.0];
}

+ (void)appendLog:(NSString *)text toTextView:(UITextView *)textView {
    if (!textView || text.length == 0) {
        return;
    }
    NSDateFormatter *formatter = [[NSDateFormatter alloc] init];
    formatter.dateFormat = @"HH:mm:ss";
    NSString *line = [NSString stringWithFormat:@"[%@] %@\n", [formatter stringFromDate:NSDate.date], text];
    dispatch_async(dispatch_get_main_queue(), ^{
        textView.text = [textView.text stringByAppendingString:line];
        if (textView.text.length > 0) {
            [textView scrollRangeToVisible:NSMakeRange(textView.text.length - 1, 1)];
        }
    });
}

+ (YTIFLYAdRequestConfig *)mediaSampleRequestConfig {
    YTIFLYAdRequestConfig *config = [[YTIFLYAdRequestConfig alloc] init];
    config.settleType = @1;
    config.bidFloor = @0.01;
    config.interactStatus = @1;
    config.appName = NSBundle.mainBundle.infoDictionary[@"CFBundleDisplayName"] ?: @"YTIFLYADLibSimple";
    config.appVersion = NSBundle.mainBundle.infoDictionary[@"CFBundleShortVersionString"] ?: @"1.0";
    config.requestTimeout = @5;
    config.idfa = [self currentIDFAString];
    YTIFLYSampleLogInfo(@"RequestConfig", @"IDFA %@", config.idfa.length > 0 ? @"已设置" : @"为空");
    return config;
}

+ (nullable NSString *)currentIDFAString {
    if (@available(iOS 14, *)) {
        if (ATTrackingManager.trackingAuthorizationStatus != ATTrackingManagerAuthorizationStatusAuthorized) {
            return nil;
        }
    } else {
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
        if (!ASIdentifierManager.sharedManager.advertisingTrackingEnabled) {
            return nil;
        }
#pragma clang diagnostic pop
    }

    NSString *idfa = ASIdentifierManager.sharedManager.advertisingIdentifier.UUIDString;
    if ([self isEmptyIDFA:idfa]) {
        return nil;
    }
    return idfa;
}

+ (BOOL)isEmptyIDFA:(nullable NSString *)idfa {
    if (![idfa isKindOfClass:NSString.class] || idfa.length == 0) {
        return YES;
    }
    NSString *trimmed = [idfa stringByTrimmingCharactersInSet:NSCharacterSet.whitespaceAndNewlineCharacterSet];
    if (trimmed.length == 0) {
        return YES;
    }
    return [[trimmed lowercaseString] isEqualToString:@"00000000-0000-0000-0000-000000000000"];
}

+ (NSString *)summaryForError:(nullable YTIFLYAdError *)error {
    if (!error) {
        return @"error=nil";
    }
    return [NSString stringWithFormat:@"code=%d desc=%@", error.errorCode, error.errorDescription ?: @"无"];
}

+ (NSString *)bidInfoSummaryForAd:(nullable YTIFLYAdBase *)ad {
    YTIFLYAdBidInfo *bidInfo = ad.bidInfo;
    if (!bidInfo) {
        return @"bidInfo=nil";
    }
    return [NSString stringWithFormat:@"bidInfo={price=%@, dealId=%@}",
                                      bidInfo.price ?: @"nil",
                                      bidInfo.dealId.length > 0 ? bidInfo.dealId : @"无"];
}

+ (void)loadImageWithURLString:(NSString *)urlString
                    completion:(void (^)(UIImage *_Nullable image, NSError *_Nullable error))completion {
    NSURL *url = urlString.length > 0 ? [NSURL URLWithString:urlString] : nil;
    if (!url) {
        NSError *error = [NSError errorWithDomain:@"YTIFLYADLibSimple"
                                             code:-1
                                         userInfo:@{NSLocalizedDescriptionKey : @"图片 URL 为空或非法"}];
        if (completion) {
            dispatch_async(dispatch_get_main_queue(), ^{
                completion(nil, error);
            });
        }
        return;
    }
    NSURLSessionDataTask *task =
        [NSURLSession.sharedSession dataTaskWithURL:url
                                  completionHandler:^(NSData *data, NSURLResponse *response, NSError *error) {
                                      UIImage *image = data.length > 0 ? [UIImage imageWithData:data] : nil;
                                      dispatch_async(dispatch_get_main_queue(), ^{
                                          if (completion) {
                                              completion(image, error);
                                          }
                                      });
                                  }];
    [task resume];
}

@end
