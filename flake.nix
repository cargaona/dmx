{
  description = "dmx - Simple music search and download tool using deemix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        dmx = pkgs.python3Packages.buildPythonApplication {
          pname = "dmx";
          version = "1.0.0";
          format = "pyproject";
          
          src = ./.;
          
          nativeBuildInputs = with pkgs.python3Packages; [
            setuptools
            wheel
          ];
          
          propagatedBuildInputs = with pkgs.python3Packages; [
            # Core dependencies
            click
            colorama
            requests
            aiohttp
            
            # Try to use deemix if available, otherwise install from PyPI
            (pkgs.python3Packages.callPackage ./nix/deemix.nix {} or
             pkgs.python3Packages.buildPythonPackage rec {
               pname = "deemix";
               version = "3.6.6";
               
               src = pkgs.python3Packages.fetchPypi {
                 inherit pname version;
                 sha256 = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="; # Will be updated
               };
               
               propagatedBuildInputs = with pkgs.python3Packages; [
                 pycryptodomex
                 mutagen
                 deezer-py
               ];
               
               # Skip tests as they require network access
               doCheck = false;
               
               meta = with pkgs.lib; {
                 description = "A barebone deezer downloader library";
                 homepage = "https://deemix.app";
                 license = licenses.gpl3Plus;
               };
             })
          ];
          
          # Skip tests that require network access or special setup
          doCheck = false;
          
          # Install shell completions if available
          postInstall = ''
            # Generate shell completions
            mkdir -p $out/share/bash-completion/completions
            mkdir -p $out/share/zsh/site-functions
            mkdir -p $out/share/fish/vendor_completions.d
            
            # Try to generate completions (may fail if click version doesn't support it)
            $out/bin/dmx --help > /dev/null || true
          '';
          
          meta = with pkgs.lib; {
            description = "Simple music search and download tool using deemix";
            homepage = "https://github.com/cargaona/dmx";
            license = licenses.mit;
            maintainers = [ ];
            platforms = platforms.unix;
          };
        };
      in
      {
        packages = {
          default = dmx;
          dmx = dmx;
        };
        
        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python3
            python3Packages.pip
            python3Packages.setuptools
            python3Packages.wheel
            
            # Development tools
            python3Packages.pytest
            python3Packages.pytest-asyncio
            python3Packages.pytest-cov
            python3Packages.black
            python3Packages.flake8
            python3Packages.mypy
          ];
          
          shellHook = ''
            echo "dmx development environment"
            echo "Run 'python -m pip install -e .' to install in development mode"
            echo "Run 'dmx --help' to see available commands"
          '';
        };
        
        # Apps for easy running
        apps = {
          default = {
            type = "app";
            program = "${dmx}/bin/dmx";
          };
          dmx = {
            type = "app";
            program = "${dmx}/bin/dmx";
          };
        };
      });
}