@ECHO OFF
SETLOCAL

SET "DIR=%~dp0"
SET "APP_HOME=%DIR%"
SET "WRAPPER_JAR=%APP_HOME%gradle\wrapper\gradle-wrapper.jar"

IF NOT EXIST "%WRAPPER_JAR%" (
  ECHO Missing "%WRAPPER_JAR%".
  ECHO Open this project with Android Studio or generate the Gradle wrapper jar.
  EXIT /B 1
)

IF DEFINED JAVA_HOME (
  SET "JAVA_EXE=%JAVA_HOME%\bin\java.exe"
) ELSE (
  SET "JAVA_EXE=java.exe"
)

"%JAVA_EXE%" -classpath "%WRAPPER_JAR%" org.gradle.wrapper.GradleWrapperMain %*

