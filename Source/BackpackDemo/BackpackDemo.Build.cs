using UnrealBuildTool;
public class BackpackDemo : ModuleRules {
	public BackpackDemo(ReadOnlyTargetRules Target) : base(Target) {
		PCHUsage = PCHUsageMode.NoSharedPCHs;
		PrivatePCHHeaderFile = "BPPch.h";
		bEnableUndefinedIdentifierWarnings = false;
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "Slate", "SlateCore" });
	}
}
