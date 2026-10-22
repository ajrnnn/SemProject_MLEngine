# Strathmore Lost & Found Android app

This is the Kotlin and Jetpack Compose mobile app project. Open this `android/` directory in Android Studio; the Python matching prototype remains in the parent repository.

## Run locally

1. Let Android Studio install any missing SDK components and finish Gradle sync.
2. Select an emulator or connected Android phone.
3. Run the `app` configuration.

For a command-line build on Windows, set `JAVA_HOME` to Android Studio's bundled `jbr` directory and run `gradlew.bat :app:assembleDebug` here. Android Studio manages its own Gradle JDK setting, so this environment variable is only needed for a separate terminal.

The package ID `com.example.strathmorelostfound` is a development placeholder. Decide the final application ID with the project owner before distribution. This starter currently has no university email sign-in, account validation, reporting, or API integration; those need server-backed implementation before real use. Do not bundle training datasets, model files, or private ownership evidence into the app.
