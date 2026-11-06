#if DEBUG
import AVFoundation
import CallHistoryFeature
import CallSettingFeature
import HomeFeature
import UIKit

public struct GuideCaptureScreen: View {
  let mode = ProcessInfo.processInfo.environment["REENO_GUIDE_SCREEN"] ?? "welcome"
  public init() {}
  public var body: some View {
    Group {
      switch mode {
      case "welcome": onboarding(forceLight: false) { WelcomScreen(nextButtonTapped: {}) }
      case "name": onboarding { RegisterNameScreen(saveName: { _ in }) }
      case "profile": onboarding { ProfileSetupScreen(previewStep: .callingName) }
      case "profile-language": onboarding { ProfileSetupScreen(previewStep: .language) }
      case "profile-level": onboarding { ProfileSetupScreen(previewStep: .level) }
      case "ai-consent": onboarding(forceLight: false) { ThirdPartyAIConsentScreen(userId: "guide-sample", accepted: {}) }
      case "microphone", "microphone-dialog": onboarding {
        MicrophonePermissionScreen(status: .notDetermined, requestTapped: {}, openSettingsTapped: {})
      }
      case "first-call": onboarding { OnboardingCallScreen(state: .preview(), continueSetup: {}, consentRequired: {}) }
      case "initial-schedule": onboarding { CallSettingSetupScreen(initialDraft: nil, saveSetting: { _ in }) }
      case "home", "home-settings": tabs(selected: 0) { HomeRootScreen(debugScenario: .completed) }
      case "home-first": tabs(selected: 0) { HomeRootScreen(debugScenario: .settingsIncomplete) }
      case "history", "history-missed": tabs(selected: 1) { CallHistoryRootScreen(animatesCharacter: false) }
      case "history-detail", "history-phrases": NavigationStack { GuideHistoryDetail() }
      case "note-draft": GuideNoteDraft()
      case "call-tab": tabs(selected: 2) { CallTabRootScreen() }
      case "call-settings", "schedule-windows", "schedule-editor": NavigationStack { CallSettingDetailScreen(maxCallsPerDay: 1) }
      default: Text("Unknown guide screen")
      }
    }
    .tint(Color.main)
    .task {
      try? await Task.sleep(for: .seconds(2))
      if mode == "microphone-dialog" { _ = await AVCaptureDevice.requestAccess(for: .audio) }
      if let value = ProcessInfo.processInfo.environment["REENO_GUIDE_SCROLL"], let offset = Double(value) {
        try? await Task.sleep(for: .seconds(1))
        Self.scroll(offset)
      }
    }
  }
  // Match OnboardingScreen: only these child screens use a light environment.
  // The window keeps the app's UIUserInterfaceStyle=Dark, including materials/system UI.
  func onboarding<V: View>(forceLight: Bool = true, @ViewBuilder content: () -> V) -> some View {
    Group {
      if forceLight { content().environment(\.colorScheme, .light) }
      else { content() }
    }
    .frame(minWidth: 0, maxWidth: .infinity, minHeight: 0, maxHeight: .infinity)
    .background(
      Image.backgroundLight.resizable().scaledToFill()
        .frame(minWidth: 0, maxWidth: .infinity, minHeight: 0, maxHeight: .infinity)
        .ignoresSafeArea(.all)
    )
  }
  func tabs<V: View>(selected: Int, @ViewBuilder content: () -> V) -> some View {
    TabView(selection: .constant(selected)) {
      Tab(String(localized: "Home", bundle: .module), systemImage: "house.fill", value: 0) { NavigationStack { if selected == 0 { content() } } }
      Tab(String(localized: "History", bundle: .module), systemImage: "clock.fill", value: 1) { NavigationStack { if selected == 1 { content() } } }
      Tab(String(localized: "call_tab_title", defaultValue: "Call", bundle: .module), systemImage: "phone.fill", value: 2) { NavigationStack { if selected == 2 { content() } } }
      Tab(String(localized: "study_note_tab_title", defaultValue: "Note", bundle: .module), systemImage: "text.book.closed.fill", value: 3) { Color.clear }
      Tab(String(localized: "App", bundle: .module), systemImage: "app.fill", value: 4) { Color.clear }
    }.background(ImageTagBackgroundView())
  }
  @MainActor static func scroll(_ offset: Double) {
    guard offset > 0 else { return }
    func descendants(_ view: UIView) -> [UIScrollView] {
      (view as? UIScrollView).map { [$0] } ?? view.subviews.flatMap(descendants)
    }
    let windows = UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.flatMap(\.windows)
    for scroll in windows.flatMap(descendants) where scroll.bounds.height > 200 && scroll.contentSize.height > scroll.bounds.height {
      let maxY = scroll.contentSize.height - scroll.bounds.height + scroll.adjustedContentInset.bottom
      scroll.setContentOffset(CGPoint(x: 0, y: min(offset, maxY)), animated: false)
    }
  }
}
#endif
