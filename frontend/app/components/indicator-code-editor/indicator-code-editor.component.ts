import { Component, ElementRef, HostListener, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute, Router } from '@angular/router';
import { autocompletion } from '@codemirror/autocomplete';
import { python } from '@codemirror/lang-python';
import { EditorState } from '@codemirror/state';
import { ConfirmationDialog } from '@geonature_common/others/modal-confirmation/confirmation.dialog';
import { basicSetup, EditorView } from 'codemirror';
import { Observable } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { CanComponentDeactivate } from '../../guards/can-deactivate.guard';
import { IndicatorDetails, IndicatorExecutionContext, ProtocolProperties } from '../../interfaces';
import { getMockExecutionContext } from '../../mocks/execution-context.mock';
import { DataService } from '../../services/data.service';
import { UtilsService } from '../../services/utils.service';
import { createCodeEditorCompletionSource } from './code-editor-autocomplete';

@Component({
  selector: 'pnx-calc-indicator-code-editor',
  templateUrl: './indicator-code-editor.component.html',
  styleUrls: ['./indicator-code-editor.component.css'],
})
export class IndicatorCodeEditorComponent implements OnInit, OnDestroy, CanComponentDeactivate {
  indicatorForm: FormGroup;
  indicator: IndicatorDetails;
  protocolProperties: ProtocolProperties;
  scope: 'campaign' | 'overview' | 'statistical-tests' = 'campaign';
  campaignVariables: string[] = [];

  private _editorView?: EditorView;
  private _executionContext: IndicatorExecutionContext = getMockExecutionContext();
  // TODO: Passer à true une fois l'endpoint backend GET /calculatrice/indicator/:id/execution-context disponible
  private readonly _useBackendExecutionContext = false;
  private _initialCode = '';
  private _isSubmitted = false;

  @ViewChild('editorContainer') set editorContainerRef(
    containerElement: ElementRef<HTMLDivElement> | undefined
  ) {
    if (containerElement && !this._editorView) {
      this._initCodeMirror(containerElement.nativeElement);
    }
  }

  constructor(
    private _data: DataService,
    private _dialog: MatDialog,
    private _formBuilder: FormBuilder,
    private _route: ActivatedRoute,
    private _router: Router,
    private _utils: UtilsService
  ) {
    this.indicatorForm = this._formBuilder.group({
      code: [''],
    });
  }

  ngOnInit() {
    this.scope = this._route.snapshot.data['scope'] || 'campaign';
    this._route.params.subscribe((routeParameters) => {
      this._data
        .getIndicatorDetails(routeParameters.indicatorId)
        .subscribe((indicatorDetails: IndicatorDetails) => {
          this.indicator = indicatorDetails;
          let codeValue = '';
          if (this.scope === 'overview') {
            codeValue = indicatorDetails.overviewSourceCode || '';
          } else if (this.scope === 'statistical-tests') {
            codeValue = indicatorDetails.statisticalTestsSourceCode || '';
          } else {
            codeValue = indicatorDetails.sourceCode || '';
          }
          this._initialCode = codeValue;
          this._isSubmitted = false;
          this._setCodeValue(codeValue);

          this._data
            .getProtocolProperties(this.indicator.protocol.id)
            .subscribe((protocolProperties: ProtocolProperties) => {
              this.protocolProperties = protocolProperties;
              this._updateExecutionContext();
            });

          if (this.scope === 'overview' || this.scope === 'statistical-tests') {
            this._data
              .getIndicatorCodeVariables(this.indicator.id)
              .subscribe((variables: string[]) => {
                this.campaignVariables = variables;
                this._updateExecutionContext();
              });
          }
        });
    });
  }

  ngOnDestroy() {
    if (this._editorView) {
      this._editorView.destroy();
    }
  }

  hasUnsavedChanges(): boolean {
    const currentCode = this.indicatorForm.controls['code'].value || '';
    return currentCode !== this._initialCode;
  }

  canDeactivate(): boolean | Observable<boolean> {
    if (this._isSubmitted || !this.hasUnsavedChanges()) {
      return true;
    }

    const dialogRef = this._dialog.open(ConfirmationDialog, {
      data: {
        message:
          'Des modifications ont été apportées au code. Voulez-vous vraiment quitter sans enregistrer ?',
        yesColor: 'warn',
      },
    });

    return dialogRef.afterClosed().pipe(map((dialogResult) => Boolean(dialogResult)));
  }

  @HostListener('window:beforeunload', ['$event'])
  onBeforeUnload(event: BeforeUnloadEvent): void {
    if (!this._isSubmitted && this.hasUnsavedChanges()) {
      event.returnValue = true;
    }
  }

  onSubmit() {
    if (this.indicatorForm.valid) {
      let saveObservable$;
      if (this.scope === 'overview') {
        saveObservable$ = this._data.editIndicatorOverviewCode(
          this.indicator.id,
          this.indicatorForm.value.code
        );
      } else if (this.scope === 'statistical-tests') {
        saveObservable$ = this._data.editIndicatorStatisticalTestsCode(
          this.indicator.id,
          this.indicatorForm.value.code
        );
      } else {
        saveObservable$ = this._data.editIndicatorCode(
          this.indicator.id,
          this.indicatorForm.value.code
        );
      }

      this._isSubmitted = true;
      saveObservable$
        .pipe(
          catchError((error) => {
            this._isSubmitted = false;
            return this._utils.handleError(error);
          })
        )
        .subscribe(() => {
          this._router.navigate(['/calculatrice/indicator', this.indicator.id, 'details']);
        });
    }
  }

  insertCode(codeSnippet: string) {
    if (this._editorView) {
      const selectionRange = this._editorView.state.selection.main;
      this._editorView.dispatch({
        changes: {
          from: selectionRange.from,
          to: selectionRange.to,
          insert: codeSnippet,
        },
        selection: { anchor: selectionRange.from + codeSnippet.length },
      });
      this._editorView.focus();
    } else {
      const text = this.indicatorForm.get('code')?.value || '';
      this.indicatorForm.get('code')?.setValue(text + codeSnippet);
    }
  }

  private _setCodeValue(codeValue: string) {
    this.indicatorForm.controls['code'].setValue(codeValue);
    if (this._editorView && this._editorView.state.doc.toString() !== codeValue) {
      this._editorView.dispatch({
        changes: {
          from: 0,
          to: this._editorView.state.doc.length,
          insert: codeValue,
        },
      });
    }
  }

  private _updateExecutionContext() {
    if (this._useBackendExecutionContext) {
      if (this.indicator?.id) {
        this._data
          .getExecutionContext(this.indicator.id, this.scope)
          .subscribe((executionContext: IndicatorExecutionContext) => {
            this._executionContext = executionContext;
          });
      }
      return;
    }

    this._executionContext = getMockExecutionContext(
      this.protocolProperties,
      this.scope,
      this.campaignVariables
    );
  }

  private _initCodeMirror(containerElement: HTMLElement) {
    const initialCode = this.indicatorForm.controls['code'].value || '';

    const startState = EditorState.create({
      doc: initialCode,
      extensions: [
        basicSetup,
        python(),
        autocompletion({
          override: [createCodeEditorCompletionSource(() => this._executionContext)],
        }),
        EditorView.updateListener.of((viewUpdate) => {
          if (viewUpdate.docChanged) {
            const currentDocText = viewUpdate.state.doc.toString();
            this.indicatorForm.controls['code'].setValue(currentDocText, {
              emitEvent: false,
            });
          }
        }),
      ],
    });

    this._editorView = new EditorView({
      state: startState,
      parent: containerElement,
    });
  }
}
