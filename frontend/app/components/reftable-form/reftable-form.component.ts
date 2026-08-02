import { Component } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { Router } from '@angular/router';
import { Validators } from '@librairies/@angular/forms';
import { catchError } from 'rxjs/operators';
import { ReferenceTable } from '../../interfaces';
import { DataService } from '../../services/data.service';
import { UtilsService } from '../../services/utils.service';

@Component({
  selector: 'pnx-calc-reftable-form',
  templateUrl: './reftable-form.component.html',
  styleUrls: ['./reftable-form.component.css'],
})
export class ReferenceTableFormComponent {
  form: FormGroup;
  file: File;

  constructor(
    private _data: DataService,
    private _formBuilder: FormBuilder,
    private _router: Router,
    private _utils: UtilsService
  ) {
    this.form = this._formBuilder.group({
      file: [null, Validators.required],
      name: ['', Validators.required],
      code: ['', Validators.required],
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
      this._data
        .createReferenceTable(
          {
            name: this.form.controls.name.value,
            code: this.form.controls.code.value,
          },
          this.file
        )
        .pipe(catchError(this._utils.handleError))
        .subscribe((data: ReferenceTable) => {
          this._router.navigate(['/calculatrice/reference-tables']);
        });
    }
  }
}
