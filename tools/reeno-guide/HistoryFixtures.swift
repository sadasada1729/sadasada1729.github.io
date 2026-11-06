#if DEBUG
@MainActor enum GuideHistoryFixtures {
  static let now = MediaKitClock.now
  static func call(_ status: CallStatus = .completed, offset: Double = -3600) -> Call {
    let date = now.addingTimeInterval(offset)
    return Call(id: "guide-\(status)-\(offset)", userId: "guide-sample", scheduleId: nil, source: .scheduled,
      createdAt: date, status: status, reportedAt: date,
      answeredAt: status == .completed ? date : nil,
      endedAt: date.addingTimeInterval(status == .completed ? 100 : 30),
      endReason: status == .completed ? .userHangUp : (status == .declined ? .declined : .missed),
      maxDurationSeconds: 120, language: .englishUS,
      summaryStatus: status == .completed ? .completed : .skipped, targetLanguage: .englishUS, profileReflectionStatus: nil)
  }
  static var setting: CallSetting {
    var windows = WeeklyTimeWindows.empty
    for day in Weekday.allCases { windows[day] = [.init(id: "guide-window", startMinutes: 480, endMinutes: 1320)] }
    return .init(id: "guide-sample", isEnabled: true, language: .englishUS, level: .beginner, voice: .neutral,
      availableWindows: windows, timeZoneIdentifier: "Asia/Tokyo", desiredCallCountPerDay: 1, updatedAt: now)
  }
  static var summary: CallSummary {
    .init(id: call().id, userId: "guide-sample", createdAt: now, updatedAt: now, model: "guide-sample",
      headline: "週末に見つけた、お気に入りのカフェ",
      summaryText: "週末に友だちとカフェへ行き、ケーキとコーヒーを楽しんだ話をしました。次は別のケーキも食べてみたい、と伝えられました。",
      language: .englishUS, learningAdvice: "好きなものや感想を、自分の言葉で話せました。過去の出来事は went を使うと自然に伝わります。",
      suggestedPhrases: [.init(kind: .rewrite, nativeText: "友だちとカフェへ行きました。", translatedText: "I went to a cafe with my friend.", sourceText: "I go to cafe with my friend.", note: "過去の出来事なので、go を went にしてみましょう。"),
        .init(kind: .tryNext, nativeText: "また行ってみたいです。", translatedText: "I'd love to go there again.", sourceText: "", note: "気に入った場所について話すときに。")],
      userTurnCount: 8, userCharacterCount: 182)
  }
}
public struct GuideHistoryDetail: View {
  public init() {}
  public var body: some View { CallHistoryDetailScreen(call: GuideHistoryFixtures.call()) }
}
public struct GuideNoteDraft: View {
  public init() {}
  public var body: some View {
    CallHistoryPhraseDraftScreen(context: .init(userId: "guide-sample", language: .englishUS, tags: [],
      currentPhraseCount: 0, nativeText: "友だちとカフェへ行きました。", translatedText: "I went to a cafe with my friend.", suggestionIndex: 0), added: { _ in })
  }
}
#endif
