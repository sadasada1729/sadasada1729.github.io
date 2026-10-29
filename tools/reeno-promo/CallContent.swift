// Capture-only adaptation of CallInProgressScreen. No CallKit or live session.
  func content() -> some View {
    VStack(spacing: 0) {
      Spacer(minLength: 20)
      VStack(spacing: 8) {
        Text("Reenoから")
          .font(.font(.zenMaruMedium, size: 25))
        Text("電話が来ています")
          .font(.font(.zenMaruBlack, size: 30))
      }
      .foregroundStyle(.white)
      .shadow(color: .black.opacity(0.22), radius: 12, y: 2)
      .padding(.horizontal, 20)

      Spacer(minLength: 16)
      CallCharacterView(phase: .connecting, isMentor: false,
                        reduceMotion: ProcessInfo.processInfo.environment["REENO_PROMO_ANIMATES"] != "1")
      Label("ちょっと、おしゃべりしよう", systemImage: "phone.badge.waveform.fill")
        .font(.font(.zenMaruMedium, size: 17))
        .foregroundStyle(.white)
        .padding(.horizontal, 20)
        .padding(.vertical, 13)
        .background(.black.opacity(0.13), in: .capsule)
        .overlay(Capsule().strokeBorder(.white.opacity(0.25), lineWidth: 1))
        .padding(.top, 8)

      Spacer(minLength: 32)
      HStack(spacing: 92) {
        promoButton("拒否", symbol: "phone.down.fill", tint: Color(red: 0.98, green: 0.28, blue: 0.25))
        promoButton("応答", symbol: "phone.fill", tint: Color(red: 0.16, green: 0.79, blue: 0.43))
      }
      .padding(.bottom, 65)
    }
  }

  func promoButton(_ title: String, symbol: String, tint: Color) -> some View {
    VStack(spacing: 13) {
      Button {} label: {
        Image(systemName: symbol)
          .font(.system(size: 33, weight: .semibold))
          .foregroundStyle(.white)
          .frame(width: 82, height: 82)
          .background(tint.gradient, in: .circle)
          .overlay(Circle().strokeBorder(.white.opacity(0.22), lineWidth: 1))
          .shadow(color: tint.opacity(0.3), radius: 18, y: 6)
      }
      .buttonStyle(.plain)
      .accessibilityLabel(title)
      Text(title)
        .font(.font(.zenMaruMedium, size: 18))
        .foregroundStyle(.white)
    }
  }
