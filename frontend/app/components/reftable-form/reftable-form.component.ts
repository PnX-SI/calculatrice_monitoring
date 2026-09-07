import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Validators } from '@librairies/@angular/forms';
import { ToastrService } from 'ngx-toastr';
import { Observable } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { ReferenceTable } from '../../interfaces';
import { DataService } from '../../services/data.service';
import { UtilsService } from '../../services/utils.service';

@Component({
  selector: 'pnx-calc-reftable-form',
  templateUrl: './reftable-form.component.html',
  styleUrls: ['./reftable-form.component.css'],
})
export class ReferenceTableFormComponent implements OnInit {
  form: FormGroup;
  file: File;
  mode: 'create' | 'edit';
  referenceTable?: ReferenceTable;

  constructor(
    private _data: DataService,
    private _formBuilder: FormBuilder,
    private _router: Router,
    private _utils: UtilsService,
    private _route: ActivatedRoute,
    private _toastr: ToastrService
  ) {
    this.form = this._formBuilder.group({
      file: [null],
      name: ['', Validators.required],
      code: ['', Validators.required],
    });
  }

  ngOnInit() {
    this._route.params.subscribe((params) => {
      if (params.reftableId === undefined) {
        this.mode = 'create';
        this.form.controls.file.setValidators(Validators.required);
        this.form.controls.file.updateValueAndValidity();
        return;
      }
      this.mode = 'edit';
      this.form.controls.code.disable();
      const reftableId: number = params.reftableId;
      this._data.getReferenceTables().subscribe((data: Array<ReferenceTable>) => {
        this.referenceTable = data.find((referenceTable) => referenceTable.id == reftableId);
        this.form.setValue({
          file: null,
          name: this.referenceTable.name,
          code: this.referenceTable.code,
        });
      });
    });
  }

  onFileChange(event) {
    let fileList: FileList = event.target.files;
    if (fileList.length < 1) {
      return;
    }
    this.file = fileList[0];
  }

  onSubmit() {
    if (this.form.valid) {
      if (this.mode === 'create') {
        this._data
          .createReferenceTable(
            {
              name: this.form.controls.name.value,
              code: this.form.controls.code.value,
            },
            this.file
          )
          .pipe(catchError((error: HttpErrorResponse) => this._handleSubmitError(error)))
          .subscribe((data: ReferenceTable) => {
            this._router.navigate(['/calculatrice/reference-tables']);
          });
      } else {
        this._data
          .editReferenceTable(
            this.referenceTable.id,
            {
              name: this.form.controls.name.value,
            },
            this.file
          )
          .pipe(catchError((error: HttpErrorResponse) => this._handleSubmitError(error)))
          .subscribe((data: ReferenceTable) => {
            this._router.navigate(['/calculatrice/reference-tables']);
          });
      }
    }
  }

  private _handleSubmitError(error: HttpErrorResponse): Observable<never> {
    const errMsg =
      error.status === 400 && error.error?.code
        ? error.error.code[0]
        : 'Une erreur est survenue lors de l’enregistrement du tableau de référence.';
    this._toastr.error(errMsg, 'Erreur', {
      disableTimeOut: true,
      tapToDismiss: false,
      closeButton: true,
      easeTime: 0,
    });
    return this._utils.handleError(error);
  }
}
