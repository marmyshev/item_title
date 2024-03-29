/******************************************************************************
* OpenLP - Open Source Lyrics Projection                                      *
* --------------------------------------------------------------------------- *
* Copyright (c) 2008-2013 Raoul Snyman                                        *
* Portions copyright (c) 2008-2013 Tim Bentley, Gerald Britton, Jonathan      *
* Corwin, Samuel Findlay, Michael Gorven, Scott Guerrieri, Matthias Hub,      *
* Meinert Jordan, Armin Köhler, Erik Lundin, Edwin Lunando, Brian T. Meyer.   *
* Joshua Miller, Stevan Pettit, Andreas Preikschat, Mattias Põldaru,          *
* Christian Richter, Philip Ridout, Simon Scudder, Jeffrey Smith,             *
* Maikel Stuivenberg, Martin Thompson, Jon Tibble, Dave Warnock,              *
* Frode Woldsund, Martin Zibricky                                             *
* --------------------------------------------------------------------------- *
* This program is free software; you can redistribute it and/or modify it     *
* under the terms of the GNU General Public License as published by the Free  *
* Software Foundation; version 2 of the License.                              *
*                                                                             *
* This program is distributed in the hope that it will be useful, but WITHOUT *
* ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or       *
* FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for    *
* more details.                                                               *
*                                                                             *
* You should have received a copy of the GNU General Public License along     *
* with this program; if not, write to the Free Software Foundation, Inc., 59  *
* Temple Place, Suite 330, Boston, MA 02111-1307 USA                          *
******************************************************************************/

#define DllExport extern "C"  __declspec( dllexport )

#define DEBUG(...)  if (debug) printf(__VA_ARGS__)

enum PPTVIEWSTATE {PPT_CLOSED, PPT_STARTED, PPT_OPENED, PPT_LOADED,
    PPT_CLOSING};

DllExport int OpenPPT(char *filename, HWND hParentWnd, RECT rect,
    char *previewPath);
DllExport BOOL CheckInstalled();
DllExport void ClosePPT(int id);
DllExport int GetCurrentSlide(int id);
DllExport int GetSlideCount(int id);
DllExport void NextStep(int id);
DllExport void PrevStep(int id);
DllExport void GotoSlide(int id, int slide_no);
DllExport void RestartShow(int id);
DllExport void Blank(int id);
DllExport void Unblank(int id);
DllExport void Stop(int id);
DllExport void Resume(int id);
DllExport void SetDebug(BOOL onOff);

LRESULT CALLBACK CbtProc(int nCode, WPARAM wParam, LPARAM lParam);
LRESULT CALLBACK CwpProc(int nCode, WPARAM wParam, LPARAM lParam);
LRESULT CALLBACK GetMsgProc(int nCode, WPARAM wParam, LPARAM lParam);
BOOL GetPPTViewerPath(char *pptViewerPath, int stringSize);
BOOL GetPPTViewerPathFromReg(char *pptViewerPath, int stringSize);
HBITMAP CaptureWindow(HWND hWnd);
VOID SaveBitmap(CHAR* filename, HBITMAP hBmp) ;
VOID CaptureAndSaveWindow(HWND hWnd, CHAR* filename);
BOOL GetPPTInfo(int id);
BOOL SavePPTInfo(int id);
void Unhook(int id);

#define MAX_PPTS 16
#define MAX_SLIDES 256

struct PPTVIEW
{
    HHOOK hook;
    HHOOK msgHook;
    HWND hWnd;
    HWND hWnd2;
    HWND hParentWnd;
    HANDLE hProcess;
    HANDLE hThread;
    DWORD dwProcessId;
    DWORD dwThreadId;
    RECT rect;
    int slideCount;
    int currentSlide;
    int firstSlideSteps;
    int lastSlideSteps;
    int steps;
    int guess;
    char filename[MAX_PATH];
    char previewPath[MAX_PATH];
    int slideNos[MAX_SLIDES];
    PPTVIEWSTATE state;
};
